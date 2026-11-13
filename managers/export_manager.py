from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from tempfile import TemporaryDirectory
import shutil
import subprocess
import imageio_ffmpeg

from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QFileDialog, QMessageBox

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import App


class ExportManager:
    def __init__(self, app: "App"):
        self.app = app

    def on_export_as_mp4(self):
        """Export the animation as an MP4 video."""
        file_path, _ = QFileDialog.getSaveFileName(
            self.app.main_window,
            "Save animation as MP4",
            "animation.mp4",
            "MP4 videos (*.mp4);;All files (*)",
        )

        if not file_path:
            return

        path = Path(file_path)
        if path.suffix.lower() != ".mp4":
            path = path.with_suffix(".mp4")

        self._export_animation_with_ffmpeg(path, "mp4", transparent=False)

    def on_export_as_gif(self):
        """Export the animation as an animated GIF."""
        file_path, _ = QFileDialog.getSaveFileName(
            self.app.main_window,
            "Save animation as GIF",
            "animation.gif",
            "GIF images (*.gif);;All files (*)",
        )

        if not file_path:
            return

        path = Path(file_path)
        if path.suffix.lower() != ".gif":
            path = path.with_suffix(".gif")

        transparent = False
        self._export_animation_with_ffmpeg(
            path, "gif", transparent=transparent)

    def on_export_as_webp(self, transparent: bool = True):
        """Export the animation as an animated WebP."""
        file_path, _ = QFileDialog.getSaveFileName(
            self.app.main_window,
            "Save animation as WebP",
            "animation.webp",
            "WebP images (*.webp);;All files (*)",
        )

        if not file_path:
            return

        path = Path(file_path)
        if path.suffix.lower() != ".webp":
            path = path.with_suffix(".webp")

        self._export_animation_with_ffmpeg(
            path, "webp", transparent=transparent)

    def _export_animation_with_ffmpeg(
        self,
        output_path: Path,
        output_type: str,
        transparent: bool,
    ):
        """Render frames to temporary PNG files and encode them with ffmpeg."""

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg is None:
            QMessageBox.critical(
                self.app.main_window,
                "Export failed",
                "ffmpeg was not found. Install ffmpeg via the Python package `imageio-ffmpeg`.",
            )
            return

        with TemporaryDirectory(prefix="animation_export_") as temp_dir:
            temp_path = Path(temp_dir)
            concat_file = temp_path / "frames.txt"

            durations: list[float] = []

            current_time = 0.0
            default_frametime = (
                self.app.timeline_manager.default_frametime
            )

            frames = self.app.timeline_manager.frames

            for i, frame in enumerate(frames):
                image = self._render_animation_frame(
                    frame_index=i,
                    current_time=current_time,
                    transparent=transparent,
                )

                frame_path = temp_path / f"frame_{i:06d}.png"

                if not image.save(str(frame_path), "PNG"):  # pyright: ignore[reportArgumentType, reportCallIssue] # nopep8   # because A. this works fine at runtime and B. because my pep8 decides to disable pyright's ignore comment
                    raise RuntimeError(
                        f"Could not save temporary frame {frame_path}"
                    )

                frametime = (
                    frame.frametime
                    if not frame.is_default
                    else default_frametime
                )

                # ffmpeg's concat demuxer expects seconds.
                frametime = max(float(frametime), 0.001)
                durations.append(frametime)

                current_time += frametime

            if not durations:
                raise RuntimeError("The animation contains no frames")

            self._write_ffmpeg_concat_file(
                concat_file,
                temp_path,
                len(durations),
                durations,
            )

            command = self._build_ffmpeg_command(
                ffmpeg=ffmpeg,
                concat_file=concat_file,
                output_path=output_path,
                output_type=output_type,
                transparent=transparent,
            )

            subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

    def _write_ffmpeg_concat_file(
        self,
        concat_file: Path,
        temp_path: Path,
        frame_count: int,
        durations: list[float],
    ):
        with concat_file.open("w", encoding="utf-8", newline="\n") as file:
            for i, duration in enumerate(durations):
                frame_path = (temp_path / f"frame_{i:06d}.png").resolve()

                # The paths are generated locally, but escape them for concat syntax.
                escaped_path = str(frame_path).replace(
                    "\\", "/").replace("'", r"'\''")

                file.write(f"file '{escaped_path}'\n")
                file.write(f"duration {duration:.6f}\n")

            # Required so that the final duration is honored.
            last_frame = (
                temp_path / f"frame_{frame_count - 1:06d}.png").resolve()
            escaped_last_frame = (
                str(last_frame)
                .replace("\\", "/")
                .replace("'", r"'\''")
            )
            file.write(f"file '{escaped_last_frame}'\n")

    def _build_ffmpeg_command(
        self,
        ffmpeg: str,
        concat_file: Path,
        output_path: Path,
        output_type: str,
        transparent: bool,
    ) -> list[str]:
        common_input = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
        ]

        if output_type == "mp4":
            # MP4 does not preserve alpha. The scale filter also ensures even
            # dimensions, which are required by yuv420p.
            return common_input + [
                "-vsync",
                "0",
                "-vf",
                "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                str(output_path),
            ]

        if output_type == "gif":
            # Two-pass palette generation gives substantially better GIF colors.
            palette_path = concat_file.with_name("palette.png")

            first_pass = common_input + [
                "-vf",
                "palettegen=stats_mode=diff",
                "-frames:v",
                "1",
                str(palette_path),
                "-vsync",
                "0",
            ]

            subprocess.run(
                first_pass,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            return [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-i",
                str(palette_path),
                "-vsync",
                "0",
                "-lavfi",
                "paletteuse=dither=sierra2_4a",
                "-loop",
                "0",
                str(output_path),
            ]

        if output_type == "webp":
            command = common_input + [
                "-c:v",
                "libwebp_anim",
                "-lossless",
                "0",
                "-q:v",
                "85",
                "-loop",
                "0",
                "-vsync",
                "0",
            ]

            if transparent:
                command += [
                    "-pix_fmt",
                    "yuva420p",
                ]
            else:
                command += [
                    "-pix_fmt",
                    "yuv420p",
                ]

            command.append(str(output_path))
            return command

        raise ValueError(f"Unsupported output type: {output_type}")

    def _render_animation_frame(
        self,
        frame_index: int,
        current_time: float,
        transparent: bool,
    ) -> QImage:
        image = QImage(
            self.app.layer_manager.size,
            QImage.Format.Format_ARGB32,
        )

        image.fill(
            Qt.GlobalColor.transparent
            if transparent
            else Qt.GlobalColor.white
        )

        layers: list[QImage] = self.app.layer_manager.composite(
            frame_index,
            current_time,
        )

        painter = QPainter(image)

        try:
            for layer in layers:
                painter.drawImage(image.rect(), layer)
        finally:
            painter.end()

        return image

    def on_export_as_image_sequence(self, imageType: str, transparent: bool):
        """Exports the animation as an image sequence."""
        file_path, _ = QFileDialog.getSaveFileName(
            self.app.main_window,
            "Save images as ZIP",
            "images.zip",
            "ZIP archives (*.zip);;All files (*)",
        )

        if not file_path:
            return  # User canceled

        path = Path(file_path)

        if path.suffix.lower() != ".zip":
            path = path.with_suffix(".zip")

        with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
            current_time: float = 0.0
            default_frametime = self.app.timeline_manager.default_frametime
            for i, frame in enumerate(self.app.timeline_manager.frames):
                new_image = self._render_animation_frame(
                    i, current_time, transparent)

                image_data = self.image_to_bytes(new_image, imageType)
                archive.writestr(f"image_{i:04d}." +
                                 imageType.lower(), image_data)
                current_time += frame.frametime if not frame.is_default else default_frametime

    def image_to_bytes(self, image: QImage, image_format: str = "PNG") -> bytes:
        """Encode a QImage into image-format bytes."""
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)

        if not image.save(buffer, image_format):  # type: ignore[arg-type]
            buffer.close()
            raise RuntimeError("Could not encode image")

        data = bytes(buffer.data().data())
        buffer.close()
        return data

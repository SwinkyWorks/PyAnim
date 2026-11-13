from PySide6.QtWidgets import QLayout


def clear_layout(layout: QLayout):
    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)
        if item != None:
            if (childWidget := item.widget()) != None:  # I love the walrus operator :)
                childWidget.deleteLater()
            layout.removeItem(item)

"""The only application UI outside the shell-hosted drawing child."""
from PySide6.QtWidgets import QMenu, QSystemTrayIcon
from PySide6.QtGui import QActionGroup


class TrayController:
    def __init__(self, icon, pause, fly, mouse, display, quit_app):
        self.tray = QSystemTrayIcon(icon)
        self.menu = QMenu()
        self.menu.addAction("Cockatiel Desktop Pet").setEnabled(False)
        self.status = self.menu.addAction("正在连接桌面…")
        self.status.setEnabled(False)
        self.menu.addSeparator()
        self.mode_menu = self.menu.addMenu("显示模式")
        self.mode_group = QActionGroup(self.mode_menu)
        self.mode_group.setExclusive(True)
        self.modes = {}
        for value, label in (("desktop", "桌面后方"), ("front", "所有应用前方"), ("hidden", "隐藏")):
            action = self.mode_menu.addAction(label)
            action.setCheckable(True)
            self.mode_group.addAction(action)
            action.triggered.connect(lambda checked=False, mode=value: display(mode))
            self.modes[value] = action
        self.menu.addSeparator()
        self.pause = self.menu.addAction("暂停", pause)
        self.fly = self.menu.addAction("立即飞行", fly)
        self.mouse = self.menu.addAction("鼠标互动：开", mouse)
        self.menu.addSeparator()
        self.menu.addAction("退出", quit_app)
        self.tray.setContextMenu(self.menu)
        self.tray.setToolTip("Cockatiel Desktop Pet")
        self.tray.show()

    def sync(self, paused, interaction, available, busy=False, mode="desktop"):
        self.pause.setText("继续" if paused else "暂停")
        self.mouse.setText("鼠标互动：开" if interaction else "鼠标互动：关")
        self.modes[mode].setChecked(True)
        self.fly.setEnabled(available and not paused and not busy)
        status = "已隐藏" if mode == "hidden" else "显示不可用，已隐藏" if not available else "已暂停" if paused else "置于所有应用前方" if mode == "front" else "位于桌面后方"
        self.status.setText(status)
        self.tray.setToolTip(f"Cockatiel Desktop Pet\n{status}")

    def unavailable(self, mode="desktop"):
        message = "桌面宿主不可用，宠物已隐藏。可在显示模式中选择所有应用前方。" if mode == "desktop" else "显示窗口不可用，宠物已隐藏，稍后自动重试。"
        self.tray.showMessage("Cockatiel Desktop Pet", message, QSystemTrayIcon.MessageIcon.Warning, 8000)

    def close(self):
        self.tray.hide()
        self.menu.close()

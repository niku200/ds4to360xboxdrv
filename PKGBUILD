# Maintainer: Your Name <youremail@example.com>
pkgname=ds4to360xboxdrv
pkgver=5.0.0
pkgrel=1
pkgdesc="Modernized DualShock 4 to Xbox 360 controller emulator using xboxdrv and evsieve with GTK4 GUI"
arch=('any')
url="https://github.com/YourUsername/ds4to360xboxdrv"
license=('MIT')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'systemd' 'xboxdrv' 'evsieve' 'polkit')
backup=('etc/ds4to360.conf')
source=("${pkgname}-${pkgver}.tar.gz::${url}/archive/v${pkgver}.tar.gz")
sha256sums=('SKIP')

package() {
  cd "${pkgname}-${pkgver}"

  # Install backend and GUI
  install -Dm755 src/backend.py "${pkgdir}/usr/share/ds4to360/backend.py"
  install -Dm755 src/gui.py "${pkgdir}/usr/share/ds4to360/gui.py"

  install -d "${pkgdir}/usr/bin"
  ln -s /usr/share/ds4to360/gui.py "${pkgdir}/usr/bin/ds4to360-gui"

  # Install systemd service
  install -Dm644 ds4-xboxdrv.service "${pkgdir}/usr/lib/systemd/system/ds4-xboxdrv.service"

  # Install udev rules
  install -Dm644 99-ds4-xboxdrv.rules "${pkgdir}/usr/lib/udev/rules.d/99-ds4-xboxdrv.rules"

  # Install desktop file
  install -Dm644 ds4to360-gui.desktop "${pkgdir}/usr/share/applications/ds4to360-gui.desktop"

  # Install default config
  install -Dm644 ds4to360.conf.example "${pkgdir}/etc/ds4to360.conf"

  # Install license
  install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}

# Maintainer: Pakrohk <pakrohk@gmail.com>
pkgname=ds4to360xboxdrv
pkgver=5.1.0
pkgrel=1
pkgdesc="Modernized DualShock 4/3 and DualSense to Xbox 360 controller emulator using xboxdrv and evsieve with GTK4/Libadwaita GUI"
arch=('any')
url="https://github.com/Pakrohk/ds4to360xboxdrv"
license=('MIT')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'systemd' 'xboxdrv' 'polkit' 'python-evdev')
optdepends=('evsieve: For better device grabbing and exclusive control')
backup=('etc/ds4to360.conf')
source=("${pkgname}-${pkgver}.tar.gz::${url}/archive/v${pkgver}.tar.gz")
sha256sums=('SKIP')

package() {
  cd "${pkgname}-${pkgver}"

  # Install package source
  install -d "${pkgdir}/usr/share/ds4to360"
  cp -r src/ds4to360 "${pkgdir}/usr/share/ds4to360/"

  # Install wrapper scripts
  install -d "${pkgdir}/usr/bin"
  cat <<EOF > "${pkgdir}/usr/bin/ds4to360-gui"
#!/bin/bash
export PYTHONPATH=\$PYTHONPATH:/usr/share/ds4to360
exec python3 -m ds4to360.gui "\$@"
EOF
  chmod +x "${pkgdir}/usr/bin/ds4to360-gui"

  cat <<EOF > "${pkgdir}/usr/bin/ds4to360-backend"
#!/bin/bash
export PYTHONPATH=\$PYTHONPATH:/usr/share/ds4to360
exec python3 -m ds4to360.backend "\$@"
EOF
  chmod +x "${pkgdir}/usr/bin/ds4to360-backend"

  # Install systemd service
  install -Dm644 ds4-xboxdrv.service "${pkgdir}/usr/lib/systemd/system/ds4-xboxdrv.service"
  sed -i "s|ExecStart=.*|ExecStart=/usr/bin/ds4to360-backend|" "${pkgdir}/usr/lib/systemd/system/ds4-xboxdrv.service"

  # Install udev rules
  install -Dm644 99-ds4-xboxdrv.rules "${pkgdir}/usr/lib/udev/rules.d/99-ds4-xboxdrv.rules"

  # Install desktop file
  install -Dm644 ds4to360-gui.desktop "${pkgdir}/usr/share/applications/ds4to360-gui.desktop"

  # Install default config
  install -Dm644 ds4to360.conf.example "${pkgdir}/etc/ds4to360.conf"

  # Install license
  install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}

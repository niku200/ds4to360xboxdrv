# Maintainer: pakrohk <pakrohk@gmail.com>
pkgname=pnp
pkgver=5.2.0
pkgrel=1
pkgdesc="PNP (PS NOT PS) – PlayStation to Xbox controller emulator for Linux using xboxdrv and evsieve with GTK4/Libadwaita GUI"
arch=('any')
url="https://github.com/pakrohk/pnp"
license=('MIT')
depends=('python' 'python-gobject' 'gtk4' 'libadwaita' 'systemd' 'xboxdrv' 'evsieve' 'polkit' 'python-evdev' 'python-pyudev')
makedepends=('uv' 'python-installer')
backup=('etc/pnp/pnp.conf')
source=("${pkgname}-${pkgver}.tar.gz::${url}/archive/v${pkgver}.tar.gz"
        "pnp.service"
        "99-pnp.rules"
        "pnp.desktop"
        "pnp.conf.example")
sha256sums=('SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP')

build() {
  cd "${pkgname}-${pkgver}"
  uv build --wheel
}

package() {
  cd "${pkgname}-${pkgver}"

  # Install the wheel
  python -m installer --destdir="$pkgdir" --prefix=/usr dist/*.whl

  # Fix shebangs and set PYTHONPATH in /usr/bin scripts
  cat <<EOF > "$pkgdir/usr/bin/pnp-gui"
#!/bin/sh
export PYTHONPATH="/usr/share/pnp:\$PYTHONPATH"
exec /usr/bin/python3 -m pnp.main "\$@"
EOF
  chmod 755 "$pkgdir/usr/bin/pnp-gui"

  cat <<EOF > "$pkgdir/usr/bin/pnp-backend"
#!/bin/sh
export PYTHONPATH="/usr/share/pnp:\$PYTHONPATH"
exec /usr/bin/python3 -m pnp.main --headless "\$@"
EOF
  chmod 755 "$pkgdir/usr/bin/pnp-backend"

  # Install systemd service
  install -Dm644 ../pnp.service "${pkgdir}/usr/lib/systemd/system/pnp.service"

  # Install udev rules
  install -Dm644 ../99-pnp.rules "${pkgdir}/usr/lib/udev/rules.d/99-pnp.rules"

  # Install desktop file
  install -Dm644 ../pnp.desktop "${pkgdir}/usr/share/applications/pnp.desktop"

  # Install default config
  install -Dm644 ../pnp.conf.example "${pkgdir}/etc/pnp/pnp.conf"

  # Install license
  install -Dm644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}

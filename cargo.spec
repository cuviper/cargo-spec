# To bootstrap from scratch, set the date from src/snapshots.txt
# e.g. 0.11.0 wants 2016-03-21
%bcond_without bootstrap
%global bootstrap_date 2016-03-21

Name:           cargo
Version:        0.11.0
Release:        1%{?dist}
Summary:        Rust's package manager and build tool
License:        ASL 2.0 or MIT
URL:            https://crates.io/

Source0:        https://github.com/rust-lang/%{name}/archive/%{version}.tar.gz#/%{name}-%{version}.tar.gz

# submodule, bundled for local installation only, not distributed
%global rust_installer c37d3747da75c280237dc2d6b925078e69555499
Source1:        https://github.com/rust-lang/rust-installer/archive/%{rust_installer}.tar.gz#/rust-installer-%{rust_installer}.tar.gz

%if %with bootstrap
%define bootstrap_base https://static.rust-lang.org/cargo-dist/%{bootstrap_date}/%{name}-nightly
Source10:       %{bootstrap_base}-x86_64-unknown-linux-gnu.tar.gz
Source11:       %{bootstrap_base}-i686-unknown-linux-gnu.tar.gz
%endif

# Use vendored crate dependencies so we can build offline.
# Created using https://github.com/alexcrichton/cargo-vendor/
# FIXME: These should all eventually be packaged on their own!
# (needs directory registries, https://github.com/rust-lang/cargo/pull/2857)
Source100:      %{name}-%{version}-vendor.tar.gz

Patch1:         cargo-0.11.0-option-checking.patch

# Only x86_64 and i686 have bootstrap packages at this time.
ExclusiveArch:  x86_64 i686
%define rust_triple %{_target_cpu}-unknown-linux-gnu

BuildRequires:  rust
BuildRequires:  make
BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  python
BuildRequires:  curl
BuildRequires:  git

%if %without bootstrap
BuildRequires:  %{name}
%endif

# Indirect dependencies for vendored -sys crates above
BuildRequires:  libcurl-devel
BuildRequires:  libgit2-devel
BuildRequires:  libssh2-devel
BuildRequires:  openssl-devel
BuildRequires:  zlib-devel
BuildRequires:  pkgconfig

%description
Cargo is a tool that allows Rust projects to declare their various dependencies
and ensure that you'll always get a repeatable build.


%prep
%setup -q

# rust-installer
%setup -q -T -D -a 1
rmdir src/rust-installer
mv rust-installer-%{rust_installer} src/rust-installer

# vendored crates
%setup -q -T -D -a 100
pushd vendor/index
sed -i.vendor -e "s#file://.*/vendor/#file://$PWD/../#g" config.json
git config user.name "Cargo Packagers"
git config user.email cargo-owner@fedoraproject.org
git commit -m "builddir patched" config.json
popd

%patch1 -p1 -b .option-checking

%if %with bootstrap
mkdir -p target/dl/
cp -t target/dl/ %{SOURCE10} %{SOURCE11}
%endif


%build

# convince libgit2-sys to use the distro libgit2
export LIBGIT2_SYS_USE_PKG_CONFIG=1

# use our offline registry
mkdir -p .cargo
export CARGO_HOME=$PWD/.cargo
export CARGO_REGISTRY_INDEX="file://$PWD/vendor/index"

# this should eventually migrate to distro policy
export RUSTFLAGS="-C opt-level=3 -g"

%configure --disable-option-checking \
  --build=%{rust_triple} --host=%{rust_triple} --target=%{rust_triple} \
  %{!?with_bootstrap:--local-cargo=/usr/bin/cargo} \
  --local-rust-root=/usr \
  %{nil}

%make_build VERBOSE=1


%install
%make_install VERBOSE=1

# Remove installer artifacts (manifests, uninstall scripts, etc.)
rm -rv %{buildroot}/%{_prefix}/lib/

# Fix the etc/ location
mv -v %{buildroot}/%{_prefix}/%{_sysconfdir} %{buildroot}/%{_sysconfdir}

# Remove unwanted documentation files (we already package them)
rm -rf %{buildroot}/%{_docdir}/%{name}/


%check
# the tests are more oriented toward in-tree contributors
#make test VERBOSE=1


%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig


%files
%license LICENSE-APACHE LICENSE-MIT LICENSE-THIRD-PARTY
%doc README.md
%{_bindir}/cargo
%{_mandir}/man1/cargo*.1*
%{_sysconfdir}/bash_completion.d/cargo
%{_datadir}/zsh/site-functions/_cargo


%changelog
* Sun Jul 17 2016 Josh Stone <jistone@fedoraproject.org> - 0.11.0-1
- Initial package, bootstrapped

%if 0%{?_with_python27_module}
%undefine _without_python3
%endif

# Note that the function of bootstrap is that it disables the test suite and whl
#   bcond_with bootstrap = tests enabled, package with whl created
%bcond_with bootstrap

%bcond_with python36_module

%bcond_with python2
%bcond_without python3

%global pypi_name wheel
%global python_wheelname %{pypi_name}-%{version}-py2.py3-none-any.whl

%if %{with python2}
%global python2_wheeldir %{_datadir}/python2-wheels
%global python2_wheelname %python_wheelname
%endif # with python2

%if %{with python3}
%global python3_wheeldir %{_datadir}/python3-wheels
%global python3_wheelname %python_wheelname
%endif # with python3

Name:           python-%{pypi_name}
Version:        0.31.1
Release:        3%{?dist}
Epoch:          1
Summary:        Built-package format for Python

License:        MIT
URL:            https://github.com/pypa/wheel
Source0:        %{url}/archive/%{version}/%{pypi_name}-%{version}.tar.gz
BuildArch:      noarch

# We need to remove wheel's own implementation of crypto due to FIPS concerns.
# See more: https://bugzilla.redhat.com/show_bug.cgi?id=1731526
# Upstream commit: https://github.com/pypa/wheel/commit/d3f5918ccbb1c79e2fc42b7766626a0aa20dc438
Patch0: removed-wheel-signing-and-verifying-features.patch

%global _description \
A built-package format for Python.\
\
A wheel is a ZIP-format archive with a specially formatted filename and the\
.whl extension. It is designed to contain all the files for a PEP 376\
compatible install in a way that is very close to the on-disk format.

%description %{_description}

%if %{with python2}
%package -n     python2-%{pypi_name}
Summary:        %{summary}
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools
%if ! %{with bootstrap}
BuildRequires:  python2-pytest
%endif
%{?python_provide:%python_provide python2-%{pypi_name}}

%description -n python2-%{pypi_name} %{_description}

Python 2 version.
%endif # with python2


%if %{with python3}
%package -n     python3-%{pypi_name}
Summary:        %{summary}
%if %{with python36_module}
BuildRequires:  python36-devel
BuildRequires:  python36-rpm-macros
%else
BuildRequires:  python3-devel
%endif
BuildRequires:  python3-setuptools
%if %{without bootstrap}
BuildRequires:  python3-pytest
%endif # without bootstrap

# Require alternatives version that implements the --keep-foreign flag
Requires(postun): alternatives >= 1.19.1-1
# For alternatives
Requires:       python36
Requires(post): python36
Requires(postun): python36

%{?python_provide:%python_provide python3-%{pypi_name}}

%description -n python3-%{pypi_name} %{_description}

Python 3 version.

%endif # with python3

%if %{without bootstrap}
%if %{with python2}
%package -n python2-%{pypi_name}-wheel
Summary:        The Python wheel module packaged as a wheel

%description -n python2-%{pypi_name}-wheel
A Python wheel of wheel to use with virtualenv.
%endif

%if %{with python3}
%package -n python3-%{pypi_name}-wheel
Summary:        The Python wheel module packaged as a wheel

%description -n python3-%{pypi_name}-wheel
A Python wheel of wheel to use with virtualenv.
%endif

%endif


%prep
%autosetup -n %{pypi_name}-%{version} -p1
# remove unneeded shebangs
sed -ie '1d' %{pypi_name}/{egg2wheel,wininst2wheel}.py


%build
%if %{with python2}
export RHEL_ALLOW_PYTHON2_FOR_BUILD=1
%py2_build

%if %{without bootstrap}
%py2_build_wheel
%endif # without bootstrap

%endif # with python2

%if %{with python3}
%py3_build

%if %{without bootstrap}
%py3_build_wheel
%endif # without bootstrap
%endif # with python3


%install
%if %{with python3}
%py3_install
mv %{buildroot}%{_bindir}/%{pypi_name}{,-%{python3_version}}
# Create an empty file to be used by `alternatives`
touch %{buildroot}%{_bindir}/%{pypi_name}-3
%endif

%if %{with python2}
export RHEL_ALLOW_PYTHON2_FOR_BUILD=1
%py2_install
mv %{buildroot}%{_bindir}/%{pypi_name}{,-%{python2_version}}
ln -s %{pypi_name}-%{python2_version} %{buildroot}%{_bindir}/%{pypi_name}-2
%endif

%if %{without bootstrap}
%if %{with python2}
mkdir -p %{buildroot}%{python2_wheeldir}
install -p dist/%{python2_wheelname} -t %{buildroot}%{python2_wheeldir}
%endif

%if %{with python3}
mkdir -p %{buildroot}%{python3_wheeldir}
install -p dist/%{python3_wheelname} -t %{buildroot}%{python3_wheeldir}
%endif

%check
rm setup.cfg

# Remove part of the test that uses the "jsonschema" package
sed -i '/jsonschema/d' tests/test_bdist_wheel.py

export LC_ALL=C.UTF-8

%if %{with python2}
export RHEL_ALLOW_PYTHON2_FOR_BUILD=1
PYTHONPATH=%{buildroot}%{python2_sitelib} py.test-2 -v --ignore build
%endif # with python2
%if %{with python3}
PYTHONPATH=%{buildroot}%{python3_sitelib} py.test-3 -v --ignore build
%endif # with python3
%endif # without bootstrap


%if %{with python3}
%post -n python3-%{pypi_name}
alternatives --add-slave python3 %{_bindir}/python%{python3_version} \
    %{_bindir}/%{pypi_name}-3 \
    %{pypi_name}-3 \
    %{_bindir}/%{pypi_name}-%{python3_version}

%postun -n python3-%{pypi_name}
# Do this only during uninstall process (not during update)
if [ $1 -eq 0 ]; then
    alternatives --keep-foreign --remove-slave python3 %{_bindir}/python%{python3_version} \
        %{pypi_name}-3
fi
%endif


%if %{with python2}
%files -n python2-%{pypi_name}
%license LICENSE.txt
%doc CHANGES.txt README.rst
%{_bindir}/%{pypi_name}-2
%{_bindir}/%{pypi_name}-%{python2_version}
%{python2_sitelib}/%{pypi_name}*
%endif

%if %{with python3}
%files -n python3-%{pypi_name}
%license LICENSE.txt
%doc CHANGES.txt README.rst
%ghost %{_bindir}/%{pypi_name}-3
%{_bindir}/%{pypi_name}-%{python3_version}
%{python3_sitelib}/%{pypi_name}*
%endif

%if %{without bootstrap}

%if %{with python2}
%files -n python2-%{pypi_name}-wheel
%license LICENSE.txt
# we own the dir for simplicity
%dir %{python2_wheeldir}/
%{python2_wheeldir}/%{python2_wheelname}
%endif

%if %{with python3}
%files -n python3-%{pypi_name}-wheel
%license LICENSE.txt
# we own the dir for simplicity
%dir %{python3_wheeldir}/
%{python3_wheeldir}/%{python3_wheelname}
%endif

%endif

%changelog
* Thu Jul 29 2021 Tomas Orsava <torsava@redhat.com> - 1:0.31.1-3
- Adjusted the postun scriptlets to enable upgrading to RHEL 9
- Resolves: rhbz#1933055

* Mon Jul 22 2019 Tomas Orsava <torsava@redhat.com> - 1:0.31.1-2
- Removed wheel's own implementation of crypto due to FIPS concerns
Resolves: rhbz#1731526

* Fri Jun 21 2019 Charalampos Stratakis <cstratak@redhat.com> - 1:0.31.1-1
- Update to 0.31.1
Resolves: rhbz#1671681

* Thu Jun 20 2019 Miro Hrončok <mhroncok@redhat.com> - 1:0.30.0-14
- Create python{2,3}-wheel-wheel packages with the wheel of wheel
Resolves: rhbz#1659550

* Thu Apr 25 2019 Tomas Orsava <torsava@redhat.com> - 1:0.30.0-13
- Bumping due to problems with modular RPM upgrade path
- Resolves: rhbz#1695587

* Thu Oct 04 2018 Lumír Balhar <lbalhar@redhat.com> - 1:0.30.0-12
- Fix alternatives - post and postun sections only with python3
- Resolves: rhbz#1633534

* Mon Oct 01 2018 Lumír Balhar <lbalhar@redhat.com> - 1:0.30.0-11
- Fix update of alternatives for wheel-3
- Resolves: rhbz#1633534

* Mon Oct 01 2018 Lumír Balhar <lbalhar@redhat.com> - 1:0.30.0-10
- Add alternatives for wheel-3
- Resolves: rhbz#1633534

* Fri Aug 17 2018 Lumír Balhar <lbalhar@redhat.com> - 1:0.30.0-9
- Remove python3 executables without full version suffix
- Resolves: rhbz#1615727

* Fri Aug 17 2018 Lumír Balhar <lbalhar@redhat.com> - 1:0.30.0-8
- Different BR for python36 module build
- Resolves: rhbz#1615727

* Wed Aug 08 2018 Lumír Balhar <lbalhar@redhat.com> - 1:0.30.0-7
- Remove unversioned binaries from python2 subpackage
- Resolves: rhbz#1613343

* Tue Aug 07 2018 Lumír Balhar <lbalhar@redhat.com> - 1:0.30.0-6
- Disable tests (enable bootstrap)
- Build Python 3 version in python27 module

* Tue Jul 03 2018 Tomas Orsava <torsava@redhat.com> - 1:0.30.0-5
- This package might be built with the non-modular python2 package from RHEL8
  buildroot and thus we need to enable it

* Tue Jun 12 2018 Petr Viktorin <pviktori@redhat.com> - 1:0.30.0-4
- Also remove test dependency on python3-jsonschema

* Wed May 30 2018 Petr Viktorin <pviktori@redhat.com> - 1:0.30.0-3
- Remove test dependency on python2-jsonschema
  https://bugzilla.redhat.com/show_bug.cgi?id=1584189

* Tue Apr 10 2018 Petr Viktorin <pviktori@redhat.com> - 1:0.30.0-2
- Remove build-time (test) dependency on python-keyring

* Fri Feb 23 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 1:0.30.0-1
- Update to 0.30.0

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.30.0a0-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Tue Aug 29 2017 Tomas Orsava <torsava@redhat.com> - 0.30.0a0-8
- Switch macros to bcond's and make Python 2 optional to facilitate building
  the Python 2 and Python 3 modules

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.30.0a0-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.30.0a0-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Jan 03 2017 Charalampos Stratakis <cstratak@redhat.com> - 0.30.0a0-5
- Enable tests

* Fri Dec 09 2016 Charalampos Stratakis <cstratak@redhat.com> - 0.30.0a0-4
- Rebuild for Python 3.6 without tests

* Tue Dec 06 2016 Igor Gnatenko <i.gnatenko.brain@gmail.com> - 0.30.0a0-3
- Add bootstrap method

* Mon Sep 19 2016 Charalampos Stratakis <cstratak@redhat.com> - 0.30.0a0-2
- Use the python_provide macro

* Mon Sep 19 2016 Charalampos Stratakis <cstratak@redhat.com> - 0.30.0a0-1
- Update to 0.30.0a0
- Added patch to remove keyrings.alt dependency

* Wed Aug 10 2016 Igor Gnatenko <ignatenko@redhat.com> - 0.29.0-1
- Update to 0.29.0
- Cleanups and fixes

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.26.0-3
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.26.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Oct 13 2015 Robert Kuska <rkuska@redhat.com> - 0.26.0-1
- Update to 0.26.0
- Rebuilt for Python3.5 rebuild

* Thu Jun 18 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.24.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Jan 13 2015 Slavek Kabrda <bkabrda@redhat.com> - 0.24.0-3
- Make spec buildable in EPEL 6, too.
- Remove additional sources added to upstream tarball.

* Sat Jan 03 2015 Matej Cepl <mcepl@redhat.com> - 0.24.0-2
- Make python3 conditional (switched off for RHEL-7; fixes #1131111).

* Mon Nov 10 2014 Slavek Kabrda <bkabrda@redhat.com> - 0.24.0-1
- Update to 0.24.0
- Remove patches merged upstream

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.22.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Fri Apr 25 2014 Matej Stuchlik <mstuchli@redhat.com> - 0.22.0-3
- Another rebuild with python 3.4

* Fri Apr 18 2014 Matej Stuchlik <mstuchli@redhat.com> - 0.22.0-2
- Rebuild with python 3.4

* Thu Nov 28 2013 Bohuslav Kabrda <bkabrda@redhat.com> - 0.22.0-1
- Initial package.

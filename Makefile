APP_ID=io.github.abukharov268.WordSeek

flatpak-bundle: build/repo
	flatpak build-bundle build/repo build/${APP_ID}.flatpak ${APP_ID}

build/repo: build/python-requirements.json build/python-build-requirements.json gnome-sdk
	flatpak-builder --repo=./build/repo --user \
		build/flatpak-build ./build_aux/flatpak/MANIFEST.yml

flatpak-install: build/python-requirements.json build/python-build-requirements.json gnome-sdk
	flatpak-builder --repo=./build/repo --user --install \
		build/flatpak-build ./build_aux/flatpak/MANIFEST.yml

flatpak-clean:
	rm -r ./build/flatpak-build/ ./build/repo

gnome-sdk:
	flatpak install flathub org.gnome.Sdk//48 org.gnome.Platform//48

build/python-requirements.json: build/requirements.txt
	python ./build_aux/flatpak-builder-tools/pip/flatpak-pip-generator \
		--runtime=org.gnome.Sdk//48 \
		--requirements-file=./build/requirements.txt \
		--output=./build/python-requirements.json

build/python-build-requirements.json:
	python ./build_aux/flatpak-builder-tools/pip/flatpak-pip-generator \
		--build-isolation \
		--ignore-installed=setuptools \
		--runtime=org.gnome.Sdk//48 \
		--requirements-file=./build_aux/flatpak/build-requirements.txt \
		--output=./build/python-build-requirements.json

build/requirements.txt: build pyproject.toml
	poetry export --without-hashes --with=gnome \
		| sed '/platform_system == "Windows"/d' \
		> ./build/requirements.txt

build:
	mkdir -p build

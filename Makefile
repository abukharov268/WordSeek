APP_ID=io.github.abukharov268.WordSeek

flatpak-bundle: build/repo
	flatpak build-bundle build/repo build/${APP_ID}.flatpak ${APP_ID}

build/repo: ./build/python-requirements.json
	flatpak-builder --repo=./build/repo --user \
		build/flatpak-build ./build_aux/flatpak/MANIFEST.yml

flatpak-install: ./build/python-requirements.json
	flatpak-builder --repo=./build/repo --user --install \
		build/flatpak-build ./build_aux/flatpak/MANIFEST.yml

flatpak-clean:
	rm -r ./build/flatpak-build/ ./build/repo

gnome-sdk:
	flatpak install flathub org.gnome.Sdk//48 org.gnome.Platform//48

./build/python-requirements.json: gnome-sdk ./build/requirements.txt
	python ./build_aux/flatpak-builder-tools/pip/flatpak-pip-generator.py\
		--build-isolation \
		--wheel-arches=x86_64 \
		--prefer-wheels=greenlet,cwcwidth,librt,ast-serialize,sqlite-icu \
		--ignore-installed=pygments \
		--runtime=org.gnome.Sdk//48 \
		--requirements-file=./build/requirements.txt \
		--output=./build/python-requirements.json

./build/requirements.txt: ./build ./pyproject.toml
	uv export --format requirements.txt \
		--no-header --no-annotate --no-editable --no-emit-local \
		--no-default-groups \
		| python ./build_aux/scripts/join_escaped_lines.py \
		> ./build/requirements.txt

./build:
	mkdir -p build

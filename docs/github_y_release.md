# GitHub y releases

El proyecto esta preparado para control de versiones y para generar un ZIP compartible.

## Crear paquete local

```powershell
.\scripts\build_release_zip.ps1
```

Salida:

```text
release/Generala-Plus-vX.Y.Z-windows.zip
```

Ese ZIP contiene el juego, launchers, assets, audio, docs y el online integrado.

## Conectar con GitHub

Si tienes GitHub CLI instalado y autenticado:

```powershell
gh repo create generala-plus --private --source=. --remote=origin --push
```

Si no tienes GitHub CLI:

1. Crea un repositorio vacio en GitHub.
2. Copia la URL del repo.
3. Ejecuta:

```powershell
git remote add origin https://github.com/TU_USUARIO/generala-plus.git
git branch -M main
git push -u origin main
```

## Crear una version para amigos

Cuando quieras publicar una version:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

El workflow de GitHub Actions crea un artifact con el ZIP. Tambien puedes subir manualmente el ZIP de `release/` a una GitHub Release.

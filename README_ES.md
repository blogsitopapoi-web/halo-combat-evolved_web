# Experimento OpenCE para Blogger: compilación sin pthreads

Este paquete es el primer cambio real de código: prepara un checkout del código fuente de OpenCE para intentar compilar el port web sin `SharedArrayBuffer` ni `PROXY_TO_PTHREAD`.

## Qué incluye

- `tools/prepare_blogger_singlethread.py`: modifica el build script y las comprobaciones del navegador de OpenCE. El parche es estricto y aborta si no encuentra exactamente el código esperado.
- `.github/workflows/build-blogger-singlethread.yml`: acción de GitHub que compila el experimento y guarda el sitio generado como artefacto.

## Cómo aplicarlo en el repositorio actual

1. Cambia a tu rama `blogger-native-test` en `blogsitopapoi-web/halo-combat-evolved_web`.
2. Descarga y extrae este ZIP en tu ordenador.
3. En GitHub, pulsa **Add file → Upload files** y sube las carpetas y archivos incluidos, respetando sus rutas (`tools/` y `.github/workflows/`). Haz el commit en `blogger-native-test`.
4. Abre la pestaña **Actions** de GitHub y abre **Build OpenCE single-thread experiment**. Ejecuta **Run workflow** si no se ejecutó automáticamente.
5. Si termina correctamente, descarga el artefacto `opence-blogger-singlethread-web-experiment`.

## Importante: estado y limitaciones

Esto **no es todavía el port nativo terminado** y no está probado en un navegador. Primero es necesario comprobar que el motor compile sin pthreads. Incluso si compila, puede requerir cambios de runtime: la versión normal usa pthreads para permitir bloqueos y ejecutar el canvas fuera del hilo principal, y el backend OPFS debe seguir funcionando. La versión nativa de Blogger también necesitará adaptar las rutas de recursos y los workers para que no dependan de rutas relativas a GitHub Pages. Este experimento evita modificar el `halo.wasm` desplegado actualmente.

No sustituye ni borra ningún archivo de tu versión de `main`. No incluye mapas ni una ISO del juego.

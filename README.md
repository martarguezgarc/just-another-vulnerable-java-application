# Configuración del Workflow SLSA Generic Generator

## Descripción
Este documento explica cómo configurar el workflow de **SLSA Generic Generator** en GitHub Actions para generar provenance (attestations) de artefactos y mejorar la seguridad de la cadena de suministro de software (Software Supply Chain Security).

El workflow utiliza el generador oficial de SLSA para producir metadata verificable sobre los artefactos generados durante el pipeline de CI/CD.

# ¿Qué es SLSA?
**SLSA (Supply-chain Levels for Software Artifacts)** es un framework de seguridad que permite:
- Garantizar la integridad de los artefactos
- Verificar cómo fue construido un artefacto
- Reducir riesgos de supply chain attacks
- Generar provenance firmada criptográficamente

## Referencias
- https://slsa.dev
- https://github.com/slsa-framework/slsa-github-generator

# Arquitectura del Workflow
El proceso se divide en dos etapas:

| **1. Build** | **2. Provenance** |
|---|---|
| - Compila la aplicación<br> - Genera artefactos<br> - Calcula hashes SHA256 | - Ejecuta el workflow reutilizable de SLSA<br> - Firma la provenance<br> - Adjunta la attestación al release |

## Requisitos
Antes de comenzar, asegúrate de contar con:
- Repositorio en GitHub
- GitHub Actions habilitado

# Configuración del Workflow
## 1. Crear Workflow
- Nos vamos al apartado Actions del repositorio y le damos a New Workflow
<img width="668" height="186" alt="image" src="https://github.com/user-attachments/assets/f37baa7d-2196-4008-80c6-7a4af0af81e6" />
<br>
- Buscamos _SLSA General Generator_ y le damos a Configurar, esto nos creará un YAML de ejemplo
<img width="1043" height="446" alt="image" src="https://github.com/user-attachments/assets/503cfa34-18eb-4e1a-9f37-367f4aa3dc2b" />
<br>
- Si nuestro proyecto está en Mave Java, cambiamos el fichero para que quede así: 
<br><br>
**Archivo:** .github/workflows/generator-generic-ossf-slsa3-publish.yml
<br>

```yaml
# This workflow uses actions that are not certified by GitHub.
# They are provided by a third-party and are governed by separate terms of service, privacy policy, and support documentation.

# This workflow lets you generate SLSA provenance file for your project.
# The generation satisfies level 3 for the provenance requirements - see https://slsa.dev/spec/v0.1/requirements
# The project is an initiative of the OpenSSF (openssf.org) and is developed at https://github.com/slsa-framework/slsa-github-generator.
# The provenance file can be verified using https://github.com/slsa-framework/slsa-verifier.
# For more information about SLSA and how it improves the supply-chain, visit slsa.dev.

name: SLSA generic generator
on:
  workflow_dispatch: # Activated manually
  release: # or when a release is created
    types: [created]

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digests: ${{ steps.hash.outputs.digests }}
      artifact-name: ${{ steps.build.outputs.artifact-name }}

    steps:
      - uses: actions/checkout@v4 # Clone the repository within the runner

      - name: Set up JDK 11
        uses: actions/setup-java@v4
        with:
          java-version: '11'
          distribution: 'temurin'

      # ========================================================
      #
      # Step 1: Build your artifacts.
      #
      # ========================================================
      - name: Build with Maven
        id: build
        run: |
          mvn clean package -DskipTests # Build the Java artifact and generate the .jar; this must be modified if the project is not Java
          ARTIFACT_NAME=$(ls target/*.jar | head -1 | xargs basename) # Locates the final files for which the hash will be calculated
          echo "artifact-name=$ARTIFACT_NAME" >> "$GITHUB_OUTPUT"
      
      - name: Generate subject digest for provenance
        id: hash
        run: |
          ARTIFACT_PATH="target/${{ steps.build.outputs.artifact-name }}"
          DIGEST=$(sha256sum "$ARTIFACT_PATH" | base64 -w0) # Calculates the SHA-256 hashes and encodes them in Base64
          echo "digests=$DIGEST" >> "$GITHUB_OUTPUT"
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: java-artifact
          path: target/${{ steps.build.outputs.artifact-name }}

      # ========================================================
      #
      # Step 2: Add a step to generate the provenance subjects as shown below. Update the sha256 sum arguments to include all binaries that you generate provenance for.
      #
      # ========================================================


 provenance:
    needs: [build]
    permissions:
      actions: read   # To read the workflow path.
      id-token: write # To sign the provenance.
      contents: write # To add assets to a release.
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.1.0 # Uses the official generator to generate the SLSA provenance for the project
    with:
      base64-subjects: "${{ needs.build.outputs.digests }}" # Passes those hashes to the provenance generation workflow
      upload-assets: true # Optional: Upload to a new release

```
El job debe:

- Compilar el proyecto
- Generar artefactos
- Calcular hashes SHA256
- Exportar los hashes como output

<img width="1560" height="165" alt="image" src="https://github.com/user-attachments/assets/b76124a7-6877-402f-a706-6b70b87b2607" />

### Explicación de Permisos

| Permiso | Descripción |
|---|---|
| `actions: read` | Permite leer metadata del workflow |
| `id-token: write` | Necesario para firma OIDC |
| `contents: write` | Permite subir attestations al release |

### Nota:
* El paso Build artifacts debe ser adaptado al build del proyecto
* Cuando se lance de forma manual, creará los artefactos pero no los subirá ya que no hay release a dónde subirlo
* Usar tags versionados y siempre referenciar versiones fijas (Usar @v1.9.0 en lugar de @main)
* Evitar Pull Requests para Provenance. SLSA no recomienda generar provenance en workflows de `pull_request` debido a restricciones de seguridad.

# Resultado Esperado

Al finalizar el workflow:
- Se generan los artefactos
- Se crea una provenance SLSA
- La provenance queda firmada
- Se adjunta un archivo:

```txt
<artifact-name>.intoto.jsonl
```

---

## Verificación de Provenance

1. Instalar el verificador oficial:

```bash
go install github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@latest
```

2. Verificar un artefacto

```bash
slsa-verifier verify-artifact \
  --provenance-path provenance.intoto.jsonl \
  --source-uri github.com/mi-org/mi-repo \
  dist/app-linux-amd64
```

---

# Referencias Oficiales
- https://slsa.dev
- https://github.com/slsa-framework/slsa-github-generator
- https://github.com/slsa-framework/slsa-github-generator/blob/main/internal/builders/generic/README.md

````

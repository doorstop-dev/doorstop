# Optional Dependencies

Doorstop has minimal core dependencies, but certain features require additional tools to be installed on your system.

## LaTeX Publishing

To publish documents in LaTeX/PDF format, you need a LaTeX distribution installed:

### Windows

Download and install [MiKTeX](https://miktex.org/download):

```powershell
winget install MiKTeX.MiKTeX
```

### Linux (Debian/Ubuntu)

```sh
sudo apt-get update
sudo apt-get install texlive-latex-base texlive-latex-extra
```

### macOS

```sh
brew install --cask mactex
```

### Verification

After installation, verify that `pdflatex` is available:

```sh
pdflatex --version
```

## PlantUML Diagrams in LaTeX

If your documents contain PlantUML diagrams (using ` ​```plantuml` code blocks) and you want to publish them to LaTeX/PDF, you need three additional tools:

1. **Java Runtime Environment** (to run PlantUML)
2. **PlantUML** (to generate diagrams)
3. **Inkscape** (to convert SVG diagrams to PDF)

### Windows Installation

```powershell
# Install Java Runtime (required for PlantUML)
winget install EclipseAdoptium.Temurin.17.JRE

# Install PlantUML
winget install PlantUML.PlantUML

# Install Inkscape (for SVG to PDF conversion)
winget install Inkscape.Inkscape
```

!!! warning "Add Inkscape to PATH"
    After installing Inkscape on Windows, you **must** add it to your PATH:
    
    1. Open **Windows Settings** → **System** → **About** → **Advanced system settings**
    2. Click **"Environment Variables"**
    3. Under **"System variables"**, select **"Path"** and click **"Edit"**
    4. Click **"New"** and add: `C:\Program Files\Inkscape\bin`
    5. Click **"OK"** to save all dialogs
    6. **Restart your terminal** for the changes to take effect

### Linux Installation (Debian/Ubuntu)

```sh
sudo apt-get update
sudo apt-get install default-jre plantuml inkscape
```

### macOS Installation

```sh
brew install openjdk plantuml inkscape
```

### Verification

Verify all dependencies are installed correctly:

```sh
java -version
plantuml -version
inkscape --version
```

## Inkscape for SVG Images

Even if you don't use PlantUML, Inkscape is still required if your documents contain SVG images that need to be converted to PDF during LaTeX compilation.

### Why Inkscape?

LaTeX (specifically `pdflatex`) cannot directly include SVG images. Doorstop's LaTeX publisher automatically converts SVG files to PDF using Inkscape during the compilation process.

!!! info "Inkscape Version Compatibility"
    Doorstop requires **Inkscape 1.0 or later**. Older versions used different command-line syntax that is not compatible.

## Troubleshooting
### Windows: "inkscape: command not found"

**Cause:** Inkscape is not in your PATH.

**Solution:**

1. Verify Inkscape is installed: Check if `C:\Program Files\Inkscape\bin\inkscape.exe` exists
2. Add to PATH as described above
3. **Restart your terminal** - existing terminals won't see the PATH changes
4. Test: `inkscape --version`

### LaTeX: "PlantUML diagram not found"

**Cause:** PlantUML diagrams require the `title` attribute.

**Solution:** Ensure all PlantUML code blocks have a title:

````markdown
```plantuml title="System Architecture"
@startuml
Alice -> Bob: Hello
@enduml
```
````

Without the `title` attribute, Doorstop cannot determine the filename for the generated diagram.

### Security Note: Shell Escape

!!! warning "Shell Escape Security"
    LaTeX publishing with PlantUML requires `pdflatex` to be run with the `-shell-escape` flag, which allows LaTeX to execute external commands (like `plantuml` and `inkscape`).
    
    The generated `compile.sh` script automatically uses this flag. Be aware of the [security implications](https://tex.stackexchange.com/questions/88740/what-does-shell-escape-do) when compiling LaTeX files from untrusted sources.

## Summary Table

| Feature                  | Required Tools                       |
| ------------------------ | ------------------------------------ |
| **LaTeX/PDF Publishing** | LaTeX distribution (MiKTeX/TeX Live) |
| **PlantUML in LaTeX**    | LaTeX + Java + PlantUML + Inkscape   |
| **SVG images in LaTeX**  | LaTeX + Inkscape                     |
| **HTML Publishing**      | *(no additional tools required)*     |
| **Markdown Publishing**  | *(no additional tools required)*     |

## Next Steps

Once you have installed the required dependencies:

- Continue with [Setup](setup.md) to create your first Doorstop project
- Learn about [Publishing Documents](../cli/publishing.md) to generate outputs
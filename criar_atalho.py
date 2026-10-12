#!/usr/bin/env python3
import os
import sys
import stat
import importlib.util

def verificar_dependencias():
    print("🔍 Verificando dependências do sistema...")
    faltando = []

    # 1. Checar Tkinter
    if importlib.util.find_spec("tkinter") is None:
        faltando.append("tkinter")

    # 2. Checar Matplotlib
    if importlib.util.find_spec("matplotlib") is None:
        faltando.append("matplotlib")

    # Se faltar alguma dependência, avisa o utilizador e orienta como instalar
    if faltando:
        print("\n⚠️ DEPENDÊNCIAS FALTANTES DETETADAS!")
        print("Para que o programa funcione corretamente, instale os pacotes necessários:\n")

        if "tkinter" in faltando:
            if sys.platform.startswith("linux"):
                print(" 📌 Para instalar o Tkinter (Linux):")
                print("    sudo apt update && sudo apt install python3-tk\n")
            else:
                print(" 📌 O Tkinter não foi encontrado no seu Python (Windows). Reinstale o Python marcando a opção 'tcl/tk'.\n")

        if "matplotlib" in faltando:
            print(" 📌 Para instalar o Matplotlib:")
            print("    pip install matplotlib\n")

        print("❌ Por favor, instale as dependências acima e execute este script novamente.")
        sys.exit(1) # Encerra o script para não criar atalho de um app que não vai abrir

    print("✅ Todas as dependências estão instaladas!\n")

# Executa a verificação antes de criar o atalho
verificar_dependencias()

# Localiza a pasta atual onde o programa está salvo
pasta_atual = os.path.dirname(os.path.abspath(__file__))
app_py = os.path.join(pasta_atual, "app.py")
icone = os.path.join(pasta_atual, "icone.png")

if sys.platform.startswith("win"):
    # ---------------- LÓGICA PARA WINDOWS ----------------
    desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
    if not os.path.exists(desktop):
        desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Área de Trabalho")

    caminho_atalho = os.path.join(desktop, "Gerenciador de Contas.lnk")

    pythonw = os.path.join(sys.prefix, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = "pythonw.exe"

    vbs_script = f'''
    Set WshShell = CreateObject("WScript.Shell")
    Set shortcut = WshShell.CreateShortcut("{caminho_atalho}")
    shortcut.TargetPath = "{pythonw}"
    shortcut.Arguments = '"{app_py}"'
    shortcut.WorkingDirectory = "{pasta_atual}"
    shortcut.IconLocation = "{icone}"
    shortcut.Description = "Gerenciador de Contas"
    shortcut.Save
    '''

    vbs_path = os.path.join(pasta_atual, "temp_shortcut.vbs")
    try:
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write(vbs_script)

        import subprocess
        subprocess.run(["cscript", "//Nologo", vbs_path], shell=True)
        if os.path.exists(vbs_path):
            os.remove(vbs_path)

        print("✅ Atalho criado com sucesso na Área de Trabalho (Windows)!")
        print(f"Local: {caminho_atalho}")

    except Exception as e:
        print(f"❌ Erro ao criar atalho no Windows: {e}")

else:
    # ---------------- LÓGICA PARA LINUX ----------------
    desktop = os.path.expanduser("~/Área de trabalho")
    if not os.path.exists(desktop):
        desktop = os.path.expanduser("~/Desktop")
    if not os.path.exists(desktop):
        os.makedirs(desktop, exist_ok=True)

    caminho_atalho = os.path.join(desktop, "GerenciadorDeContas.desktop")

    conteudo_desktop = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Gerenciador de Contas
Comment=Gerenciador de Contas Pessoais
Exec=python3 "{app_py}"
Icon={icone}
Path={pasta_atual}
Terminal=false
StartupNotify=true
"""

    try:
        with open(caminho_atalho, "w", encoding="utf-8") as f:
            f.write(conteudo_desktop)

        st = os.stat(caminho_atalho)
        os.chmod(caminho_atalho, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        print("✅ Atalho criado com sucesso na Área de Trabalho (Linux)!")
        print(f"Local: {caminho_atalho}")

    except Exception as e:
        print(f"❌ Erro ao criar atalho no Linux: {e}")

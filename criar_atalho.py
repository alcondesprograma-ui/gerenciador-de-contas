#!/usr/bin/env python3
import os
import sys
import stat
import subprocess
import importlib.util

def verificar_e_instalar_dependencias():
    print("🔍 Verificando dependências do sistema...")

    # 1. Verificar e instalar Tkinter
    if importlib.util.find_spec("tkinter") is None:
        print("⚠️ 'tkinter' não encontrado. Tentando instalar...")
        if sys.platform.startswith("linux"):
            try:
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", "python3-tk"], check=True)
                print("✅ 'tkinter' instalado com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao instalar tkinter automaticamente: {e}")
                print("Por favor, instale manualmente rodando: sudo apt install python3-tk")
        else:
            print("❌ 'tkinter' é obrigatório, mas não pôde ser instalado automaticamente no Windows.")

    # 2. Verificar e instalar Matplotlib
    if importlib.util.find_spec("matplotlib") is None:
        print("⚠️ 'matplotlib' não encontrado. Instalando via pip...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "matplotlib"], check=True)
            print("✅ 'matplotlib' instalado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao instalar matplotlib: {e}")
            print("Por favor, instale manualmente rodando: pip install matplotlib")

# Executa a verificação antes de criar o atalho
verificar_e_instalar_dependencias()

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

# 1. Ativar a Interface Web do VLC
## No computador que fará a projeção, você precisa habilitar o controle remoto do VLC:
- Abra o VLC e vá em Ferramentas > Preferências (ou Ctrl + P).
- No canto inferior esquerdo, em Exibir configurações, marque Tudo.
- No menu lateral esquerdo, vá em Interface > Interfaces Principais e marque a caixa Web.
- Expanda o menu Interfaces Principais, clique em Lua.
- Em Lua HTTP, defina uma senha (ex: 1234).
- Reinicie o VLC.
  
- Para testar se funcionou, abra o navegador e acesse http://localhost:8080. Ele pedirá usuário e senha (deixe o usuário em branco e coloque a senha que você definiu).
---

# 🚀 Guia de Lançamento (Release) - Monitor de Votação

Este repositório está configurado com um fluxo de automação via GitHub Actions. Sempre que uma nova versão do código for finalizada, o sistema compilará automaticamente o projeto Python e gerará um executável portátil para Linux (`.AppImage`), publicando-o na página de Releases.

---

## 📦 Como gerar uma nova versão

O gatilho para a Action iniciar a compilação é a criação de uma **Tag Git** que comece com a letra `v` (ex: `v1.0.0`, `v1.1`, `v2.0-beta`).

### Passo a Passo pelo Terminal

**1. Commit suas alterações finais**
Certifique-se de que todo o código está testado e commitado na branch principal:

```bash
git add .
git commit -m "feat: adiciona terminal de logs na interface"
git push origin main

```

**2. Crie a Tag da versão**
Crie uma tag para marcar este ponto na história do código. O nome da tag **deve obrigatoriamente** começar com `v` para que a Action reconheça:

```bash
git tag v1.0.0

```

**3. Envie a Tag para o repositório**
O comando `git push` tradicional não envia tags. Você precisa enviá-la explicitamente para acionar o servidor:

```bash
git push origin v1.0.0

```

*(Dica: Se quiser enviar todas as tags criadas localmente de uma vez, use `git push --tags`)*

---

## ⚙️ O que acontece em seguida?

Assim que a tag for enviada, vá até a aba **Actions** do repositório. Você verá o fluxo `Gerar AppImage Linux` em execução. Este processo leva cerca de 2 a 3 minutos e realiza as seguintes etapas de forma invisível:

* Configura o ambiente Ubuntu com Python 3.10.
* Instala as dependências do sistema (`python3-tk`) e do projeto (`requests`, `pyinstaller`).
* Compila o código-fonte em um binário único.
* Empacota o binário com o `appimagetool`.
* Publica o arquivo final na seção **Releases** (na lateral direita da página inicial do repositório).

---

## 🐧 Como executar o arquivo gerado (Linux)

Após baixar o arquivo `Monitor_Votacao-x86_64.AppImage` da página de Releases, é necessário conceder permissão de execução antes de abri-lo pela primeira vez.

**Via Terminal:**

```bash
# Dá permissão de execução
chmod +x Monitor_Votacao-x86_64.AppImage

# Executa o aplicativo
./Monitor_Votacao-x86_64.AppImage

```

**Via Interface Gráfica:**

1. Clique com o botão direito sobre o arquivo `.AppImage`.
2. Vá em **Propriedades** > **Permissões**.
3. Marque a caixa **"Permitir execução do arquivo como um programa"**.
4. Dê um clique duplo no arquivo para iniciar o Monitor.

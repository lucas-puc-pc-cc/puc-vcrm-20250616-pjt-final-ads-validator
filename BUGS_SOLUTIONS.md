# Erro ao Instalar `dlib` via `pip` e Como Resolver

Durante a instalação dos requisitos Python de um projeto, a instalação do pacote `dlib` falhou devido à ausência do CMake no sistema.

## Ambiente

| SO                  | Kernel            |
| ------------------- | ----------------- |
|  Ubuntu 24.04.2 LTS | 6.11.0-26-generic |


## Erro Apresentado

```bash
Building wheel for dlib (pyproject.toml) ... error
error: subprocess-exited-with-error
...
CMake is not installed on your system!
...
More generally, cmake is not installed if when you open a terminal window
and type `cmake --version` you get an error.
```

## Causa

O pacote `dlib` depende de C++ e precisa **compilar o código-fonte localmente**. Para isso, o **CMake** é obrigatório, assim como algumas ferramentas de build.

## Solução

1. **Instalar o `cmake` e ferramentas de build**

    Para sistemas baseados em Ubuntu/Debian:
    ```sh
    sudo apt update
    sudo apt install cmake build-essential python3-dev libboost-all-dev
    ```

2. **Reinstalar os requisitos**

    Após a instalação dos pacotes de sistema acima, volte a tentar instalar os requisitos  
    ```sh
    pip install -r requirements...
    ```

---
---
---
# 🎧 SonoPlay — Efeitos Sonoros para Celular

App web (PWA) que toca **8 efeitos sonoros reais**, cada um com um **botão
próprio**. Feito para rodar em aparelhos celulares, funciona **offline** e é
instalável pela tela inicial.

## Efeitos

| Botão | Efeito | Arquivo |
|---|---|---|
| 🌩️ | Tempestade forte e vento uivando | `audio/01-tempestade.mp3` |
| 👊 | Três batidas fortes, secas e pausadas | `audio/02-batidas.mp3` |
| 😰 | Suspense/tensão — fraca e aumentada | `audio/03-suspense.mp3` |
| 🍶 | Coisas quebrando: xícaras, garrafas | `audio/04-quebra.mp3` |
| 🪟 | Janela se abrindo | `audio/05-janela.mp3` |
| 👣 | Passos leves no chão | `audio/06-passos.mp3` |
| 🚪 | Porta se abrindo com um estrondo | `audio/07-porta.mp3` |
| 🎹 | Piano melancólico com cordas entrando | `audio/08-melancolico.mp3` |

Os áudios são **gratuitos para uso comercial**, vindos da Mixkit — os 7
efeitos sob a *Sound Effects Free License* e o piano melancólico sob a
*Stock Music Free License*. Ver [`CREDITS.md`](CREDITS.md) para a licença
completa e a origem de cada arquivo.

## Arquivos

```
index.html            app completo (UI + reprodução + fallback sintético)
audio/*.mp3           os 8 efeitos sonoros (1,3 MB no total)
manifest.webmanifest  manifesto PWA (instalável)
sw.js                 service worker (cache offline)
icon.svg / -192/-512  ícones do app
CREDITS.md            licença e créditos dos áudios
test_*.py             testes Playwright (replay, RMS, offline, visualizador…)
README.md             este arquivo
```

## Como usar

**1. Abra o arquivo** — basta abrir `index.html` no navegador.

**2. Como app instalável (recomendado)** — publique a pasta num servidor com
HTTPS, abra no celular e use **“Adicionar à tela inicial”**.

**3. Servir localmente na rede**

```bash
cd sonoplastia
python3 -m http.server 8090
# no celular: http://<ip-do-pc>:8090
```

> O cache offline só ativa em `http://`/`https://`. Aberto como `file://` o
> app funciona normalmente, apenas sem instalar.

## Controles

- **Botão do efeito** — inicia a reprodução; tocar **o mesmo** botão de novo
  interrompe só ele (podem tocar vários efeitos ao mesmo tempo)
- **■ Parar** — encerra tudo imediatamente
- **Volume 🔊** — volume geral
- **Volume 😰 Suspense** — volume **exclusivo** do suspense, ajustável até
  enquanto ele toca; fica salvo entre sessões
- **∞** — o suspense toca **em loop** até você parar (badge ∞ no botão e tag
  “∞ loop” na linha dele); os outros efeitos tocam uma vez e terminam
- Visualizador de onda mostra o sinal em tempo real

## Como funciona a reprodução

1. Ao abrir a página, os 8 MP3 são baixados e **decodificados** para
   `AudioBuffer` (≈ 9 MB de PCM em memória).
2. Cada toque cria um `AudioBufferSourceNode` ligado a um *bus* próprio →
   volume master → compressor → analisador → saída.
3. O *bus* individual permite cortar qualquer efeito instantaneamente sem
   afetar os outros.
4. **Fallback**: se algum MP3 falhar, o botão toca automaticamente a versão
   **sintetizada em tempo real** com Web Audio API (osciladores, ruído,
   filtros e envelopes) — o app nunca fica mudo.

## Normalização dos áudios

Todos os arquivos foram tratados com ffmpeg para volumes consistentes:

- compressor leve (`threshold=-26dB, ratio=5, attack=1ms`)
- `loudnorm` em dois passos, modo linear → **−18 LUFS**, **−2 dBTP**
- MP3 192 kbps / 44,1 kHz

Medido após o processamento: loudness **−18,2 a −21,3 LUFS** (variação ≤ 3 dB)
e pico **−2,2 a −7,5 dBFS**, sem clipping.

## API pública

```js
SonoPlay.list                      // [{ id, icon, name, desc }, ...]
await SonoPlay.play("door")        // toca pelo id
SonoPlay.stop()                    // para tudo
SonoPlay.setVolume(0.6)            // volume geral 0..1
SonoPlay.setSusVolume(0.3)         // volume só do suspense 0..1 (em tempo real)
SonoPlay.susVolume                 // 0..1
SonoPlay.state                     // "running" | "suspended" | ...
SonoPlay.loaded                    // { state, buffers, total }
SonoPlay.current                   // id do último efeito ativado (null = nada)
SonoPlay.level()                   // RMS atual (0..1)
```

> `storm`, `hits`, `window`, `steps`, `break`, `door` e `sad` tocam uma vez;
> `sus` **repete em loop** até `SonoPlay.stop()` ou tocar o botão de novo.

Ids: `storm`, `hits`, `sus`, `break`, `window`, `steps`, `door`, `sad`.

## Testes

Validado com Playwright em viewport de celular (390×844), largo e paisagem:

- 8/8 arquivos carregados e decodificados
- 8/8 botões reproduzem áudio real (RMS medido entre 0,10 e 0,22)
- Duração da barra de progresso igual à do arquivo em todos os casos
- Tocar → parar → **tocar de novo** funciona (o botão nunca “morre”)
- Ao fim natural do som, o estado é liberado sozinho (`SonoPlay.current` → `null`)
- Dois efeitos simultâneos mostram “2 tocando” e somem juntos no Parar
- **Loop do suspense**: ainda tocando 13,5 s depois (arquivo tem 11 s) e o
  volume exclusivo dele altera o RMS em tempo real (`test_loop.py`)
- Botão Parar encerra tudo · zero erros de console
- Service worker registrado e cache offline funcionando

## Estrutura do som (fallback sintético)

Caso queira ajustar a síntese, cada efeito é uma receita própria:

- **Tempestade** — ruído em bandpass com varredura + LFO (uivo), leito grave
  em lowpass e trovões com filtro descendo de 1300 → 90 Hz.
- **Três batidas** — seno 155→42 Hz + estalo em highpass + médio em bandpass.
- **Suspense** — drone em serra desafinado (55 / 55,9 / 82,4 Hz) com lowpass
  abrindo, mais tom ascendente 220→720 Hz com tremolo.
- **Quebrando** — impacto + estouro em bandpass e ~28 “cacos” aleatórios.
- **Janela** — ruído em bandpass subindo 750→1550 Hz com tremolo de atrito.
- **Passos** — 6 impactos com lowpass em ~620 Hz e arranhão leve.
- **Porta** — rangido em serra com LFO de irregularidade + estrondo 125→36 Hz.
- **Melancólico** — pad em Lá menor (110 / 130,8 / 164,8 / 220 Hz) + melodia.

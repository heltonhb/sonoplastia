# Créditos e licença dos áudios

Todo o áudio do **SonoPlay** vem da biblioteca **Mixkit** (Envato): os 7
efeitos sonoros sob a **Mixkit Sound Effects Free License** e a trilha do
botão 🎹 sob a **Mixkit Stock Music Free License**. Ambas permitem uso
comercial gratuito, sem exigir atribuição.

## Fonte

- Efeitos: <https://mixkit.co/free-sound-effects/> → *Sound Effects Free License*
- Música: <https://mixkit.co/free-stock-music/> → *Stock Music Free License*
- Licenças: <https://mixkit.co/license/>

## Termos resumidos (extraídos do texto oficial da licença)

**Permitido — gratuito para projetos comerciais e não comerciais:**

- Vídeos no YouTube, redes sociais, anúncios, conteúdo educacional
- Videoclipes, projetos comerciais, produção de filmes
- **Video games**, transmissões de TV e rádio, CDs e DVDs
- Baixar, copiar, modificar, distribuir e executar publicamente os efeitos
  em plataformas web/social, podcasts, jogos, filmes e apresentações

**Não permitido:**

- Redistribuir o efeito isolado, como *stock*, dentro de uma ferramenta ou
  template, ou junto com os arquivos de origem
- Reivindicar os efeitos como próprios ou registrá-los em serviços de
  gestão de direitos

> O SonoPlay é um *produto final* que incorpora os efeitos junto com
> interface, lógica e tratamento próprio — não é uma revenda de biblioteca
> de sons. Ainda assim: **não extraia e redistribua os MP3 isoladamente.**

Atribuição não é exigida pela licença, mas os créditos são listados abaixo
por boa prática.

## Arquivos utilizados

| # | Arquivo no app | Mixkit ID | Título original | Tratamento |
|---|---|---|---|---|
| 1 | `audio/01-tempestade.mp3` | 2407 | Strong wild wind in a storm | compressão leve + loudnorm −18 LUFS |
| 2 | `audio/02-batidas.mp3` | 2182 | Wood hard hit *(3× com pausas)* | reamostrado e remixado com ffmpeg |
| 3 | `audio/03-suspense.mp3` | 786 | Cinematic suspense swell | corte para 11 s + loudnorm |
| 4 | `audio/04-quebra.mp3` | 759 | Glass break with hammer thud | compressão + loudnorm |
| 5 | `audio/05-janela.mp3` | 191 | Wooden long sliding door | compressão + loudnorm |
| 6 | `audio/06-passos.mp3` | 542 | Footsteps on heels on the pavement | compressão + loudnorm |
| 7 | `audio/07-porta.mp3` | 195 + 194 | Creaky door open + Slamming a door | concatenado (rangido → estrondo) |
| 8 | `audio/08-melancolico.mp3` | 614 | **Silent Descent** — Eugenio Mininni *(Mixkit Stock Music)* | trecho 0:38–0:50 (12 s) + compressão + loudnorm |

> Antes do item 8 usava-se o Mixkit 700 *“Baby toy music box lullaby”* (uma
> nana); a trilha foi trocada por pedido. O arquivo antigo está preservado em
> `audio_original_backup/08-melancolico-nana-corte-12s.mp3`.

### Download direto dos originais

```
efeitos:  https://assets.mixkit.co/active_storage/sfx/<ID>/<ID>-preview.mp3
música:   https://assets.mixkit.co/music/<ID>/<ID>.mp3
```

Ex.: <https://assets.mixkit.co/active_storage/sfx/759/759-preview.mp3> ·
<https://assets.mixkit.co/music/614/614.mp3>

O trecho de 12 s da música é regenerável com
`python3 make_melancolico.py 38 audio/08-melancolico.mp3`.

## Tratamento aplicado

Todos os arquivos passaram por:

1. **Compressor leve** — `acompressor=threshold=-26dB:ratio=5:attack=1:release=140`
   (pega transientes agudos e reduz o fator de crista)
2. **Loudness normalizado** — `loudnorm` em dois passos, modo linear,
   alvo **−18 LUFS**, true-peak **−2 dBTP**
3. Reencode **MP3 192 kbps / 44,1 kHz**

Resultado medido: loudness entre **−18,2 e −21,3 LUFS** (variação ≤ 3 dB),
pico entre **−2,2 e −7,5 dBFS** — nenhum arquivo estoura.

## Efeitos sintéticos (fallback)

O código JavaScript com a síntese em tempo real (Web Audio API) foi
mantido como **fallback**: se algum MP3 não carregar — sem rede, arquivo
apagado — o botão toca a versão sintetizada automaticamente. Não há
terceiros envolvidos nesses sons.

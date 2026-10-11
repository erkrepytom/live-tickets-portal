# Carrossel de ingressos e busca por data

## Editar sem programação — opção principal

1. Abra `live-tickets-editable.html` no navegador para editar o portal completo. Clique no botão de edição e procure **Carrossel de eventos — imagens e links**.
2. Para usar apenas o carrossel e a busca, abra `carousel-ingressos-editavel.html` e expanda **Editar carrossel — imagens e links**.
3. Selecione um dos 13 slides. Troque o título, descrição, texto do botão e descrição acessível da imagem.
4. Escolha uma imagem do computador ou cole uma URL HTTPS. Prefira imagens horizontais de 1920 × 600 pixels. O upload incorpora a imagem no arquivo exportado.
5. Cole o link de afiliado correto. Se mudar o destino, marque a confirmação do novo link.
6. Clique em **Aplicar slide**. Use **Adicionar slide**, **Excluir slide**, **Mover antes** e **Mover depois** para ajustar a sequência.
7. Escolha o tempo entre slides, de 3 a 60 segundos. O padrão é 6 segundos.
8. Salve neste navegador e exporte o HTML público para publicar. Exporte também o HTML editável ou um backup para guardar suas alterações.

**Salvar no navegador não atualiza o site hospedado.** Substitua o HTML na hospedagem após exportar. A versão editável deve ser guardada por você; o arquivo público não inclui seu painel de edição.

## Publicar o portal completo

1. Extraia `live-tickets-para-hospedagem.zip`.
2. Envie o `index.html` da raiz para a pasta principal da hospedagem, normalmente `public_html`, `www` ou `htdocs`.
3. Abra o endereço HTTPS do site e confira o carrossel e a busca. O `index.html` já contém suas imagens e código; não depende de bibliotecas externas.
4. No Linktree, mantenha ou troque o botão que aponta para o portal conforme o endereço de hospedagem escolhido.

## Usar apenas o carrossel em outra página

1. Abra `carousel-ingressos-editavel.html`, faça suas alterações e clique em **Exportar HTML público**.
2. Envie `carousel-public.html` para sua hospedagem.
3. No editor HTML da outra página, insira:

```html
<iframe
  src="/carousel-public.html"
  title="Explore eventos e ingressos"
  style="width:100%;height:650px;border:0;border-radius:12px"
  loading="lazy">
</iframe>
```

O conteúdo do iframe é responsivo. Aumente sua altura se desejar mostrar resultados longos da busca dentro dele. Uma alternativa é publicar o HTML público como uma página independente, que acomoda os resultados naturalmente.

## Editar o código — opção adicional

O arquivo HTML independente inclui todo o CSS e JavaScript. Procure o script `embeddedConfig` e o array **carouselSlides**. Há um comentário `CARROSSEL EDITÁVEL` no JavaScript explicando os campos:

```js
{
  title: "Formula 1",
  description: "Explore race weekends and ticket availability.",
  cta: "Get Tickets",
  href: "https://sportsevents365.com/?a_aid=6821d72fcdbe3",
  alt: "Illustrative racing cars in different colors",
  image: "https://seu-site.com/imagens/formula-1.jpg"
}
```

No JSON do HTML, mantenha aspas duplas e não use vírgula após o último item. As imagens incorporadas usam `asset:...` e o mapa `carouselAssets`. Você pode substituí-las por URLs HTTPS. Os arquivos `carousel.css` e `carousel.js` acompanham a entrega como referência do componente; o HTML único já contém ambos, portanto não os carregue novamente nele.

## Busca por ingressos

- Pesquisa por equipe, esporte, competição, cidade, local e artista quando essas informações constam nos eventos cadastrados.
- Oferece todas as datas, hoje, próximos 7 dias, próximos 30 dias e intervalo personalizado.
- Pesquisa os cartões Top events / Top Sellers e os eventos importados pelo feed configurado. Os banners representam categorias e não criam jogos, datas ou estoque.
- Não consulta automaticamente a base da SportsEvents365. Sem API ou feed conectado, a disponibilidade e a compra são verificadas no catálogo do fornecedor.
- Todos os botões iniciais do carrossel preservam o link geral de afiliado fornecido. Não foram inventados links específicos para cada competição.

## Acessibilidade e imagens

O carrossel tem textos alternativos, botões nomeados, setas de teclado, indicadores, gesto de deslizar no celular e botão de pausa. A rotação pausa com o mouse, com foco do teclado e quando a aba fica oculta. A preferência por movimento reduzido desativa a rotação inicial e as transições.

As 13 imagens são ilustrações geradas por IA, com equipes, artistas e escudos genéricos. Não representam comprovação de parceria oficial, evento específico ou disponibilidade de ingressos. Os títulos estão no HTML para continuarem editáveis. Os prompts acompanham os arquivos de imagem.

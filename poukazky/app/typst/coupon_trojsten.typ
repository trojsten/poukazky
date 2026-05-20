#import "@preview/cades:0.3.1": qr-code

#set page(paper: "a4", margin: 0cm)
#set text(font: "Source Sans 3")
#set par(spacing: 1.5em)
#show heading: it => {it + v(5mm)}

#let semibold = text.with(weight: "semibold")

// #let ctx = (
//   (amount: 10, code: "9X9E-AYL7-3CTF-RG8T"),
//   (amount: 20, code: "GCAJ-MDA3-BNN7-G9QB"),
//   (amount: 30, code: "AJG7-REJY-A9FM-BQ4J"),
// )

#let ctx = json(bytes(sys.inputs.context))

#let out = ()

#for chunk in ctx.coupons.chunks(3) {
  for i in range(3) {
    if i >= chunk.len() {
      out.push(box(width: 100%)[])
      continue
    }

    let d = chunk.at(i)
    out.push(box(width: 100%)[
      #place(center + horizon, image("assets/background_trojsten.svg"))

      #place(
        center + horizon,
        dy: 24pt,
      )[
        #text(font: "Reckless", size: 130pt)[#d.amount EUR]
        #place(top+right, text(size: 28pt)[\*])
      ]

      #v(0.2cm)
    ])
  }

  for i in range(3) {
    if i >= chunk.len() {
      out.push(box(width: 100%)[])
      continue
    }

    let d = chunk.at(i)
    out.push(box(width: 80%)[
      = Trojsten poukážka

      Túto poukážku si vieš vymeniť za poukážku do jedného z populárnych obchodov#super[1] podľa tvojho výberu do dátumu jej expirácie.
      Viac informácií nájdeš na stránke:

      #pad(7.5mm, grid(
        columns: 3,
        column-gutter: 1.5cm,

        qr-code("https://poukazky.trojsten.sk/" + d.code + "/", width: 3cm),
        rotate(90deg, reflow: true, box(width: 3cm, grid(
          columns: (1fr, auto, 1fr),
          column-gutter: 2.5mm,

          align(horizon + center, line(length: 100%, stroke: (paint: luma(100), thickness: 1pt, dash: "dotted"))),
          align(horizon + center, text(size: 0.7em)[ALEBO]),
          align(horizon + center, line(length: 100%, stroke: (paint: luma(100), thickness: 1pt, dash: "dotted")))
        ))),
        [
          Choď na *poukazky.trojsten.sk* a zadaj kód:

          #text(font: "Source Code Pro", weight: "semibold", size: 1.2em, d.code)
        ]
      ))

      #set text(fill: luma(100))
      #super[1] Aktuálne to zahŕňa #semibold[Alzu], #semibold[Martinus] a #semibold[iHRYsko], ale dostupné poukážky sa môžu časom meniť.
    ])
  }
}

#table(
  columns: 1fr,
  rows: 33.33333%,
  stroke: (x, y) => (
    top: if calc.rem(y, 3) != 0 {(thickness: 0.5pt, paint: luma(0), dash: "dashed")},
    rest: 0pt
  ),
  align: center + horizon,
  inset: -1pt,
  ..out
)

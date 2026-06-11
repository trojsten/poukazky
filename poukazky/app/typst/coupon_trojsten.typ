#import "@preview/cades:0.3.1": qr-code

#set page(paper: "a4", margin: 0cm)
#set text(font: "Source Sans 3")
#set par(spacing: 1.5em)
#show heading: it => {it + v(5mm)}

#let semibold = text.with(weight: "semibold")

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

      Túto poukážku nevieš priamo uplatniť v obchode, no vieš si ju #semibold[vymeniť] za poukážky, ktoré sa použiť dajú.
      Momentálne si môžeš vybrať medzi poukážkami do #semibold[iHRYska], #semibold[Martinusu] a #semibold[Alzy].

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
          Choď čo najskôr na *poukazky.trojsten.sk* a zadaj kód:

          #text(font: "Source Code Pro", weight: "semibold", size: 1.2em, d.code)

          Tak zistíš, že akú má Tvoja poukážka expiráciu, t. j. do kedy si ju vieš vymeniť.
        ]
      ))

      V prípade akýchkoľvek otázok alebo pripomienok nám napíš na *poukazky\@trojsten.sk*.
    ])
  }
}

#table(
  columns: 1fr,
  rows: (100% - 4mm) / 3,
  row-gutter: 2mm,
  stroke: 0pt,
  align: center + horizon,
  inset: -1pt,
  ..out
)

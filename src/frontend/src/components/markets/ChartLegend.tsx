import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

export function ChartLegend() {
  return (
    <Accordion multiple={false}>
      <AccordionItem value="legend" className="border rounded-lg px-4">
        <AccordionTrigger className="text-sm font-medium py-3">
          Jak czytać wykresy?
        </AccordionTrigger>
        <AccordionContent>
          <div className="grid md:grid-cols-2 gap-6 text-sm text-muted-foreground pb-2">
            <div className="space-y-3">
              <h4 className="font-semibold text-foreground">Wykres ceny (górny panel)</h4>
              <ul className="space-y-1.5">
                <li><span className="text-indigo-400 font-medium">Linia indigo</span> — Aktualna cena z cieniowaniem obszaru</li>
                <li><span className="text-amber-400 font-medium">Przerywana amber</span> — SMA 50 (średnia 50 sesji). Cena powyżej = trend wzrostowy; poniżej = trend spadkowy.</li>
                <li><span className="text-green-500 font-medium">▲ zielony trójkąt</span> — Sygnał BUY wygenerowany przez system</li>
                <li><span className="text-red-500 font-medium">▼ czerwony trójkąt</span> — Sygnał SELL wygenerowany przez system</li>
              </ul>
            </div>

            <div className="space-y-3">
              <h4 className="font-semibold text-foreground">RSI (dolny panel)</h4>
              <ul className="space-y-1.5">
                <li>Skala 0–100. Mierzy siłę ruchu cenowego.</li>
                <li><span className="text-red-400 font-medium">Powyżej 70 (OB)</span> — Wykupienie. Cena wzrosła za szybko, ryzyko korekty.</li>
                <li><span className="text-green-400 font-medium">Poniżej 30 (OS)</span> — Wyprzedanie. Cena spadła za bardzo, potencjalne odbicie.</li>
              </ul>

              <h4 className="font-semibold text-foreground mt-4">Statystyki pod wykresem</h4>
              <ul className="space-y-1.5">
                <li><span className="font-medium">Trend (ADX):</span> &gt;25 = rynek w trendzie; &lt;25 = rynek boczny.</li>
                <li><span className="font-medium">Weekly:</span> Trend tygodniowy — szerszy kontekst dla sygnałów dziennych.</li>
              </ul>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}

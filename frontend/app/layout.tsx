import "./globals.css";

export const metadata = {
  title: "Charon FX Dashboard",
  description: "Currency and metals dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="mx-auto max-w-6xl px-6 py-8">
          <header className="mb-8">
            <h1 className="text-3xl font-semibold">Charon FX</h1>
            <p className="text-slate-400">Daily NBP exchange signals.</p>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}

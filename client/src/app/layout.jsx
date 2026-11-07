import "./globals.css";

export const metadata = {
  title: "RAGLens | Intelligent document conversations",
  description: "Ask your documents. Get answers you can verify."
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}

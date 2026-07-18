import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AlgoTrade AI Terminal",
  description: "Institutional-grade dual-engine algorithmic trading dashboard.",
};

import { AlertProvider } from '../contexts/AlertContext';
import { NativeAppShell } from '../components/NativeAppShell';
import { ChatWidget } from '../components/ChatWidget';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.className}>
      <body>
        <NativeAppShell>
          <AlertProvider>
            {children}
            <ChatWidget />
          </AlertProvider>
        </NativeAppShell>
      </body>
    </html>
  );
}

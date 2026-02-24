import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Wrench,
  Cpu,
  Activity,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Forge Dashboard",
  description: "The universal AI agent runtime dashboard",
};

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "#", label: "Sessions", icon: MessageSquare },
  { href: "#", label: "Tools", icon: Wrench },
  { href: "#", label: "Models", icon: Cpu },
  { href: "#", label: "Traces", icon: Activity },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-950 text-gray-100 min-h-screen flex">
        {/* Sidebar */}
        <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col fixed h-full">
          <div className="p-6 border-b border-gray-800">
            <h1 className="text-xl font-bold text-orange-400">Forge</h1>
            <p className="text-xs text-gray-500 mt-1">AI Agent Runtime</p>
          </div>
          <nav className="flex-1 p-4 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:text-gray-100 hover:bg-gray-800 transition-colors"
              >
                <item.icon size={18} />
                <span className="text-sm">{item.label}</span>
              </Link>
            ))}
          </nav>
          <div className="p-4 border-t border-gray-800 text-xs text-gray-600">
            Forge v0.1.0
          </div>
        </aside>

        {/* Main content */}
        <main className="flex-1 ml-64 p-8">{children}</main>
      </body>
    </html>
  );
}

import { Link, Outlet, useLocation } from 'react-router-dom';
import { LayoutDashboard, Search, User, Shield, Menu, X } from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/utils/cn';

export default function MainLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const location = useLocation();

  const navItems = [
    { name: '仪表盘', path: '/', icon: LayoutDashboard },
    { name: '合约审计', path: '/analyzer', icon: Search },
  ];

  return (
    <div className="flex h-screen bg-background text-gray-100 overflow-hidden">
      {/* Sidebar */}
      <aside 
        className={cn(
          "bg-surface border-r border-gray-700 transition-all duration-300 flex flex-col",
          isSidebarOpen ? "w-64" : "w-16"
        )}
      >
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-700">
          {isSidebarOpen && <span className="font-bold text-xl text-primary">SC Analyzer</span>}
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-1 hover:bg-gray-700 rounded">
            {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        <nav className="flex-1 py-4">
          <ul className="space-y-2 px-2">
            {navItems.map((item) => (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
                    location.pathname === item.path 
                      ? "bg-primary/20 text-primary" 
                      : "text-gray-400 hover:bg-gray-700 hover:text-white"
                  )}
                >
                  <item.icon size={20} />
                  {isSidebarOpen && <span>{item.name}</span>}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-surface border-b border-gray-700 flex items-center justify-between px-6">
          <h2 className="text-lg font-medium">智能合约安全审计平台</h2>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">v1.0.0</span>
            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
              <User size={16} />
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

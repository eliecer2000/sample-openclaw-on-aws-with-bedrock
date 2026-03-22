import { ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { MessageSquare, User, BarChart3, Puzzle, FileText, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import ClawForgeLogo from './ClawForgeLogo';
import clsx from 'clsx';

const NAV = [
  { label: 'Chat', href: '/portal', icon: <MessageSquare size={20} /> },
  { label: 'My Profile', href: '/portal/profile', icon: <User size={20} /> },
  { label: 'My Usage', href: '/portal/usage', icon: <BarChart3 size={20} /> },
  { label: 'My Skills', href: '/portal/skills', icon: <Puzzle size={20} /> },
  { label: 'My Requests', href: '/portal/requests', icon: <FileText size={20} /> },
];

export default function PortalLayout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="flex w-64 flex-col border-r border-dark-border bg-dark-sidebar">
        {/* Logo */}
        <div className="flex h-16 items-center gap-3 border-b border-dark-border px-4">
          <ClawForgeLogo size={32} animate="idle" />
          <div>
            <div className="text-sm font-semibold text-text-primary">ClawForge Portal</div>
            <div className="text-xs text-text-muted">{user?.name || 'Employee'}</div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {NAV.map(item => (
            <button
              key={item.href}
              onClick={() => navigate(item.href)}
              className={clsx(
                'flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors',
                location.pathname === item.href
                  ? 'bg-primary/10 text-primary-light font-medium'
                  : 'text-text-secondary hover:bg-dark-hover hover:text-text-primary'
              )}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* User + Logout */}
        <div className="border-t border-dark-border p-3">
          <div className="flex items-center gap-3 rounded-lg px-3 py-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-500/20 text-blue-400 text-sm font-medium">
              {user?.name?.[0] || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">{user?.name}</p>
              <p className="text-xs text-text-muted truncate">{user?.positionName}</p>
            </div>
            <button onClick={() => { logout(); navigate('/login'); }} className="text-text-muted hover:text-text-primary">
              <LogOut size={16} />
            </button>
          </div>
          <p className="text-[10px] text-text-muted text-center mt-1">wjiad@aws · aws-samples</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}

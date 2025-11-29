import React from 'react';
import { 
  LayoutDashboard, 
  Database, 
  Brain, 
  Zap, 
  FlaskConical, 
  Beaker, 
  Rocket,
  Settings,
  User
} from 'lucide-react';
import { cn } from '../lib/utils';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  path: string;
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, path: '/' },
  { id: 'datasets', label: 'Datasets', icon: Database, path: '/datasets' },
  { id: 'models', label: 'Models', icon: Brain, path: '/models' },
  { id: 'training', label: 'Training', icon: Zap, path: '/training' },
  { id: 'testing', label: 'Testing', icon: FlaskConical, path: '/testing' },
  { id: 'experiments', label: 'Experiments', icon: Beaker, path: '/experiments' },
  { id: 'deployments', label: 'Deployments', icon: Rocket, path: '/deployments' },
];

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const [activeItem, setActiveItem] = React.useState('dashboard');

  return (
    <div className={cn(
      "bg-dark-bg-secondary border-r border-dark-border flex flex-col transition-all duration-300",
      collapsed ? "w-[80px]" : "w-[240px]"
    )}>
      {/* Logo Section */}
      <div className="h-[60px] flex items-center justify-between px-20 border-b border-dark-border">
        {!collapsed && (
          <div>
            <h1 className="text-h3 font-bold bg-gradient-to-r from-accent-primary to-accent-info bg-clip-text text-transparent">
              PEFT Studio
            </h1>
            <p className="text-tiny text-dark-text-tertiary">v1.0.0</p>
          </div>
        )}
        {collapsed && (
          <div className="text-h2 font-bold bg-gradient-to-r from-accent-primary to-accent-info bg-clip-text text-transparent mx-auto">
            PS
          </div>
        )}
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 py-20 px-12 space-y-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeItem === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => setActiveItem(item.id)}
              className={cn(
                "nav-item w-full",
                isActive && "nav-item-active",
                collapsed && "justify-center"
              )}
              title={collapsed ? item.label : undefined}
            >
              <Icon 
                size={20} 
                className={cn(
                  "transition-colors",
                  isActive ? "text-accent-primary" : "text-dark-text-tertiary"
                )} 
              />
              {!collapsed && (
                <span className="text-body">{item.label}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className="border-t border-dark-border p-12 space-y-4">
        {/* System Status */}
        {!collapsed && (
          <div className="px-8 py-12 bg-dark-bg-tertiary rounded-lg">
            <p className="text-tiny text-dark-text-tertiary mb-8">System Status</p>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-tiny mb-2">
                  <span className="text-dark-text-secondary">GPU</span>
                  <span className="text-accent-success">45%</span>
                </div>
                <div className="h-4 bg-dark-bg-primary rounded-full overflow-hidden">
                  <div className="h-full bg-accent-success w-[45%]"></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-tiny mb-2">
                  <span className="text-dark-text-secondary">RAM</span>
                  <span className="text-accent-info">62%</span>
                </div>
                <div className="h-4 bg-dark-bg-primary rounded-full overflow-hidden">
                  <div className="h-full bg-accent-info w-[62%]"></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* Settings Button */}
        <button className={cn("nav-item w-full", collapsed && "justify-center")}>
          <Settings size={20} className="text-dark-text-tertiary" />
          {!collapsed && <span className="text-body">Settings</span>}
        </button>
        
        {/* User Section */}
        <button className={cn(
          "flex items-center gap-12 w-full p-8 rounded-lg hover:bg-dark-bg-tertiary transition-all",
          collapsed && "justify-center"
        )}>
          <div className="w-32 h-32 bg-gradient-to-br from-accent-primary to-accent-info rounded-full flex items-center justify-center">
            <User size={16} className="text-white" />
          </div>
          {!collapsed && (
            <div className="flex-1 text-left">
              <p className="text-small font-medium">User</p>
              <p className="text-tiny text-dark-text-tertiary">user@email.com</p>
            </div>
          )}
        </button>
      </div>
    </div>
  );
};

export default Sidebar;

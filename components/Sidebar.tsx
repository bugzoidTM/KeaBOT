import React from 'react';
import { NavLink } from 'react-router-dom';

const Sidebar: React.FC = () => {
  const navItems = [
    { name: 'Chat', path: '/', icon: 'chat_bubble' }, // Using root for chat as primary
    { name: 'History', path: '/history', icon: 'schedule' },
    { name: 'Skills', path: '/skills', icon: 'cut' },
    { name: 'Automations', path: '/automations', icon: 'memory' },
    { name: 'Settings', path: '/settings', icon: 'settings' },
  ];

  const recentChats = [
    "Refactoring Auth Service",
    "Python Script Help",
    "React Component State",
    "Analyze JSON Structure"
  ];

  return (
    <aside className="w-72 bg-[#111a22] border-r border-[#233648] flex-col hidden md:flex h-full shrink-0 transition-all duration-300 ease-in-out relative z-20">
      {/* Header */}
      <div className="p-5 flex items-center gap-3 border-b border-[#233648]/50">
        <div 
          className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 shadow-lg ring-2 ring-[#233648]" 
          style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuCMBZXwbr2po-wT-Y2_GoHwb6gb9wbQ26bRGNsZ632CLX41kZ_HCF3avDa2I-Weyr5N7BnEgHBvsqq-Vkwj6C-OsYnA4O5xwRRazB9S6-oRvgfa-zsb-3-eMFZB7kHR6iV8Fuivmne6Sa1BEBV1CJ4Er9Fi_eEp41dUuhzwR4CIqIhycsXMfPxkagReDHshUTIH09r_EFwGokr5qljGMPLoKGQ0U25jx7BCcBhhRyAxU_c-KDQ2HB2ROu7NtHJGKFHztvnlubNyj-A")' }}
        ></div>
        <div className="flex flex-col">
          <h1 className="text-white text-lg font-bold leading-none tracking-tight">KeaBOT</h1>
          <p className="text-[#92adc9] text-xs font-normal mt-1">Pro Workspace</p>
        </div>
      </div>

      {/* Nav */}
      <div className="flex-1 overflow-y-auto py-4 flex flex-col gap-6 px-3">
        <div className="flex flex-col gap-1">
          <p className="px-3 text-xs font-semibold text-[#5a7690] uppercase tracking-wider mb-2">Apps</p>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all group ${
                  isActive
                    ? 'bg-[#233648] text-primary border border-primary/20 shadow-sm'
                    : 'text-[#92adc9] hover:bg-[#1c2a38] hover:text-white'
                }`
              }
            >
              <span className={`material-symbols-outlined text-[20px] transition-transform group-hover:scale-110`}>
                {item.icon}
              </span>
              <span className="text-sm font-medium">{item.name}</span>
            </NavLink>
          ))}
        </div>

        <div className="flex flex-col gap-1 mt-2">
          <p className="px-3 text-xs font-semibold text-[#5a7690] uppercase tracking-wider mb-2">Recent Chats</p>
          {recentChats.map((chat, idx) => (
            <a key={idx} href="#" className="px-3 py-2 rounded-lg text-[#92adc9] hover:bg-[#1c2a38] hover:text-white text-sm truncate block transition-colors">
              {chat}
            </a>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="p-3 mt-auto border-t border-[#233648]/50 flex flex-col gap-1">
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-[#92adc9] hover:bg-[#1c2a38] hover:text-white transition-all cursor-pointer">
          <div className="size-6 rounded-full bg-gradient-to-tr from-primary to-purple-500 flex items-center justify-center text-[10px] font-bold text-white">US</div>
          <div className="flex flex-col overflow-hidden">
            <span className="text-sm font-medium truncate">User Profile</span>
            <span className="text-[10px] truncate opacity-60">user@example.com</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
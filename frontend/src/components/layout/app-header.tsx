export function AppHeader() {
    return (
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex min-h-16 max-w-7xl items-center justify-between px-6">
          <div>
            <p className="text-lg font-semibold tracking-tight text-slate-950">
              CareLens
            </p>
  
            <p className="text-xs text-slate-500">
              Clinical analysis platform
            </p>
          </div>
  
          <div className="text-xs font-medium uppercase tracking-wider text-slate-400">
            Internal preview
          </div>
        </div>
      </header>
    );
  }
"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { HelpCircle } from "lucide-react";

interface ClarificationOption {
  id: string;
  title: string;
  description: string;
  example?: string;
}

interface ClarificationDialogProps {
  query: string;
  options: ClarificationOption[];
  onSelect: (option: ClarificationOption) => void;
  onClose: () => void;
}

export function ClarificationDialog({ query, options, onSelect, onClose }: ClarificationDialogProps) {
  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="bg-zinc-900 text-white border-zinc-800 max-w-2xl">
        <DialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
              <HelpCircle className="w-5 h-5 text-amber-400" />
            </div>
            <DialogTitle className="text-2xl">Clarify Your Query</DialogTitle>
          </div>
          <DialogDescription className="text-zinc-400 text-base">
            Your query <span className="text-purple-400 font-semibold">"{query}"</span> could mean multiple things. Please select what you're looking for:
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 mt-6">
          {options.map((option) => (
            <button
              key={option.id}
              onClick={() => onSelect(option)}
              className="w-full p-5 text-left rounded-xl bg-zinc-800 border border-zinc-700 hover:border-purple-500 hover:bg-zinc-800/80 transition-all group"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-bold text-lg mb-1 group-hover:text-purple-300 transition-colors">
                    {option.title}
                  </h4>
                  <p className="text-sm text-zinc-400 mb-2">
                    {option.description}
                  </p>
                  {option.example && (
                    <p className="text-xs text-zinc-500 font-mono bg-zinc-900 px-3 py-2 rounded-lg inline-block">
                      Example: {option.example}
                    </p>
                  )}
                </div>
                <div className="ml-4 text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity">
                  →
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="mt-6 flex justify-end">
          <Button onClick={onClose} variant="outline">
            Cancel
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

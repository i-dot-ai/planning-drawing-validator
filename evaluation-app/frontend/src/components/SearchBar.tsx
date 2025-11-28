import React, { memo } from "react";
import { Input, IconButton, Icon, Box } from "@chakra-ui/react";
import { Search, X } from "lucide-react";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export const SearchBar = memo(function SearchBar({
  value,
  onChange,
  placeholder = "Search...",
}: SearchBarProps) {
  return (
    <Box position="relative">
      <Box
        position="absolute"
        left={3}
        top="50%"
        transform="translateY(-50%)"
        pointerEvents="none"
      >
        <Icon as={Search} boxSize={3.5} color="fg.muted" />
      </Box>
      <Input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        variant="outline"
        size="sm"
        pl={10}
        pr={value ? 8 : 3}
      />
      {value && (
        <Box
          position="absolute"
          right={1}
          top="50%"
          transform="translateY(-50%)"
        >
          <IconButton
            aria-label="Clear search"
            size="xs"
            variant="ghost"
            onClick={() => onChange("")}
          >
            <Icon as={X} boxSize={3} />
          </IconButton>
        </Box>
      )}
    </Box>
  );
});

import React from "react";
import { Box } from "@chakra-ui/react";

interface OrganicBackdropProps {
  children: React.ReactNode;
}

export const OrganicBackdrop: React.FC<OrganicBackdropProps> = ({
  children,
}) => {
  return (
    <Box
      position="relative"
      minH="100vh"
      overflow="hidden"
      bg="bg.canvas"
      display="flex"
      flexDirection="column"
    >
      <Box
        position="relative"
        zIndex={1}
        flex={1}
        display="flex"
        flexDirection="column"
      >
        {children}
      </Box>
    </Box>
  );
};

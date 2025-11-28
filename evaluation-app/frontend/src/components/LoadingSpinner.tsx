import React from "react";
import { Spinner, VStack, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";

const MotionVStack = motion(VStack);

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
}

export function LoadingSpinner({ size = "md" }: LoadingSpinnerProps) {
  return <Spinner size={size} color="gray.600" />;
}

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "Loading..." }: LoadingStateProps) {
  return (
    <MotionVStack
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      minH="400px"
      justify="center"
      align="center"
      gap={6}
      py={24}
      borderRadius="xl"
      borderWidth="2px"
      borderStyle="dashed"
      borderColor="gray.200"
      bg="white"
    >
      <Spinner size="xl" color="gray.900" />
      <Text fontSize="sm" color="fg.muted">
        {message}
      </Text>
    </MotionVStack>
  );
}

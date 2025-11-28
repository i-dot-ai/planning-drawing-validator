import React from "react";
import { Box, HStack, VStack, Text } from "@chakra-ui/react";
import { Upload, FileSearch, CheckCircle2 } from "lucide-react";
import { keyframes } from "@emotion/react";
import { UploadStatusType } from "../../types";

interface StageIndicatorProps {
  status: UploadStatusType;
  message: string;
}

const spin = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

const pulse = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
`;

interface Stage {
  id: UploadStatusType;
  label: string;
  icon: typeof Upload;
}

const stages: Stage[] = [
  { id: "uploading", label: "Upload", icon: Upload },
  { id: "validating", label: "Validation", icon: FileSearch },
  { id: "complete", label: "Complete", icon: CheckCircle2 },
];

/**
 * StageIndicator displays the current processing stage with visual indicators.
 *
 * Shows a clear three-stage progression: Upload → Validation → Complete
 * Includes animated icons and status messages for each stage.
 */
export const StageIndicator: React.FC<StageIndicatorProps> = ({
  status,
  message,
}) => {
  // Determine which stage is active
  const getCurrentStageIndex = () => {
    if (status === "uploading") return 0;
    if (status === "validating") return 1;
    if (status === "complete") return 2;
    return 0;
  };

  const currentStageIndex = getCurrentStageIndex();
  const isError = status === "error";

  return (
    <Box
      borderRadius="xl"
      borderWidth="1px"
      borderColor={
        isError ? "rgba(220, 38, 38, 0.24)" : "rgba(79, 134, 113, 0.24)"
      }
      bg={isError ? "rgba(254, 242, 242, 0.64)" : "rgba(236, 245, 240, 0.64)"}
      p={{ base: 4, md: 5 }}
      role="status"
      aria-live="polite"
      aria-label={message}
    >
      <VStack gap={4} align="stretch">
        {/* Status message */}
        <Text fontSize="md" fontWeight="500" color="fg.emphasis">
          {message}
        </Text>

        {/* Stage indicators */}
        {!isError && (
          <HStack gap={0} justify="space-between" position="relative">
            {stages.map((stage, index) => {
              const isActive = index === currentStageIndex;
              const isComplete = index < currentStageIndex;
              const IconComponent = stage.icon;

              return (
                <React.Fragment key={stage.id}>
                  <VStack gap={2} flex={1} position="relative">
                    {/* Icon */}
                    <Box
                      display="flex"
                      alignItems="center"
                      justifyContent="center"
                      w="40px"
                      h="40px"
                      borderRadius="full"
                      bg={
                        isComplete
                          ? "brand.600"
                          : isActive
                            ? "rgba(79, 134, 113, 0.22)"
                            : "rgba(79, 134, 113, 0.08)"
                      }
                      borderWidth={isActive ? "2px" : "1px"}
                      borderColor={
                        isComplete || isActive
                          ? "brand.600"
                          : "rgba(79, 134, 113, 0.2)"
                      }
                      transition="all 0.3s"
                      animation={
                        isActive
                          ? `${pulse} 2s ease-in-out infinite`
                          : undefined
                      }
                    >
                      <Box
                        as={IconComponent}
                        boxSize={5}
                        color={
                          isComplete
                            ? "white"
                            : isActive
                              ? "brand.600"
                              : "rgba(79, 134, 113, 0.4)"
                        }
                        animation={
                          isActive && stage.id === "validating"
                            ? `${spin} 2s linear infinite`
                            : undefined
                        }
                      />
                    </Box>

                    {/* Label */}
                    <Text
                      fontSize="xs"
                      fontWeight={isActive ? "600" : "500"}
                      color={
                        isComplete || isActive ? "fg.emphasis" : "fg.muted"
                      }
                      textAlign="center"
                    >
                      {stage.label}
                    </Text>
                  </VStack>

                  {/* Connector line between stages */}
                  {index < stages.length - 1 && (
                    <Box
                      w="100%"
                      flex={1}
                      h="2px"
                      bg={isComplete ? "brand.600" : "rgba(79, 134, 113, 0.2)"}
                      transition="all 0.3s"
                      alignSelf="flex-start"
                      mt="20px"
                    />
                  )}
                </React.Fragment>
              );
            })}
          </HStack>
        )}
      </VStack>
    </Box>
  );
};

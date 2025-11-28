import React, { memo, useState, useEffect } from "react";
import {
  Box,
  Flex,
  HStack,
  Button,
  IconButton,
  Icon,
  Spinner,
} from "@chakra-ui/react";
import { toast } from "sonner";
import {
  Activity,
  History,
  FileCode,
  Play,
  Square,
  Tag,
  Settings,
  BarChart3,
  Upload,
} from "lucide-react";
import { api, APIError } from "@/lib/api";
import { zIndex, layout } from "@/lib/design-tokens";
import { GroundTruthModal } from "./GroundTruthModal";

interface HeaderProps {
  viewMode: "run" | "history" | "prompts" | "compare";
  setViewMode: (mode: "run" | "history" | "prompts" | "compare") => void;
  connectionStatus: "disconnected" | "connecting" | "connected";
  dataDir?: string;
  groundTruthPath?: string;
  currentModelName?: string;
  onDataDirSelect?: (path: string) => void;
  onGroundTruthSelect?: (path: string, labelCount: number) => void;
  onOpenRunConfig?: () => void;
  isRunning?: boolean;
  onStart?: () => void;
  onStop?: () => void;
  onReset?: () => void;
  loadedRunInfo?: {
    run_id: string;
    start_time: string;
    accuracy?: number;
  } | null;
}

export const Header = memo(function Header({
  viewMode,
  setViewMode,
  connectionStatus,
  dataDir,
  groundTruthPath,
  currentModelName,
  onDataDirSelect,
  onGroundTruthSelect,
  onOpenRunConfig,
  isRunning,
  onStart,
  onStop,
  onReset,
  loadedRunInfo,
}: HeaderProps) {
  const [showGroundTruthModal, setShowGroundTruthModal] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFileCount, setUploadedFileCount] = useState(0);
  const [groundTruthLabelCount, setGroundTruthLabelCount] = useState(0);
  const showRunControls = viewMode === "run";

  useEffect(() => {
    const loadGroundTruthCount = async () => {
      if (!groundTruthPath) {
        setGroundTruthLabelCount(0);
        return;
      }
      try {
        const data = await api.groundTruth.getGroundTruth(groundTruthPath);
        setGroundTruthLabelCount(data.entries?.length || 0);
      } catch (error) {
        console.error("Failed to load ground truth count:", error);
      }
    };
    loadGroundTruthCount();
  }, [groundTruthPath]);

  const tabs = [
    { id: "run" as const, label: "Run", icon: Activity },
    { id: "history" as const, label: "History", icon: History },
    { id: "compare" as const, label: "Compare", icon: BarChart3 },
    { id: "prompts" as const, label: "Prompts", icon: FileCode },
  ];

  const handleUpload = async () => {
    const input = document.createElement("input");
    input.type = "file";
    input.multiple = true;
    input.accept = ".pdf,.png,.jpg,.jpeg";

    input.onchange = async (e: any) => {
      const files = e.target.files;
      if (!files || files.length === 0) return;

      setIsUploading(true);
      try {
        const data = await api.documents.uploadDocuments(files);
        if (data.data_dir && onDataDirSelect) {
          onDataDirSelect(data.data_dir);
        }
        setUploadedFileCount(data.file_count || files.length);
      } catch (error) {
        const message =
          error instanceof APIError
            ? error.detail || error.message
            : "Failed to upload files";
        toast.error(message);
      } finally {
        setIsUploading(false);
      }
    };

    input.click();
  };

  return (
    <>
      <Box
        as="header"
        borderBottom="1px"
        borderColor="gray.200"
        bg="white"
        position="sticky"
        top={0}
        zIndex={zIndex.sticky}
      >
        <Flex
          align="center"
          justify="space-between"
          maxW={layout.maxWidth.content}
          mx="auto"
          px={layout.containerPadding.x}
          h={12}
        >
          {/* Left: Navigation */}
          <HStack gap={1}>
            {tabs.map((tab) => {
              const isActive = viewMode === tab.id;
              return (
                <Button
                  key={tab.id}
                  onClick={() => setViewMode(tab.id)}
                  size="sm"
                  variant="ghost"
                  color={isActive ? "gray.900" : "gray.500"}
                  fontWeight={isActive ? "semibold" : "medium"}
                  borderRadius="sm"
                  _hover={{ color: "gray.900", bg: "gray.100" }}
                  _active={{ bg: "gray.200" }}
                  position="relative"
                  px={3}
                >
                  <Icon as={tab.icon} boxSize={4} mr={2} />
                  {tab.label}
                  {isActive && (
                    <Box
                      position="absolute"
                      bottom={0}
                      left={3}
                      right={3}
                      h="2px"
                      bg="gray.900"
                      borderRadius="full"
                    />
                  )}
                </Button>
              );
            })}
          </HStack>

          {/* Right: Actions */}
          <HStack gap={2}>
            {showRunControls && (
              <>
                {/* Upload */}
                <Button
                  onClick={handleUpload}
                  disabled={isUploading}
                  size="sm"
                  variant="ghost"
                  color="gray.600"
                  fontWeight="medium"
                  _hover={{ color: "gray.900", bg: "gray.100" }}
                >
                  {isUploading ? (
                    <Spinner size="xs" color="gray.400" mr={2} />
                  ) : (
                    <Icon as={Upload} boxSize={4} mr={2} />
                  )}
                  {dataDir ? `${uploadedFileCount}` : "Upload"}
                </Button>

                {/* Labels */}
                <Button
                  onClick={() => setShowGroundTruthModal(true)}
                  size="sm"
                  variant="ghost"
                  color="gray.600"
                  fontWeight="medium"
                  _hover={{ color: "gray.900", bg: "gray.100" }}
                >
                  <Icon as={Tag} boxSize={4} mr={2} />
                  {groundTruthLabelCount > 0
                    ? `${groundTruthLabelCount}`
                    : "Labels"}
                </Button>

                {/* Primary Action: Start/Stop */}
                <Button
                  onClick={isRunning ? onStop : onStart}
                  disabled={!isRunning && !dataDir}
                  size="sm"
                  bg={isRunning ? "red.500" : "gray.900"}
                  color="white"
                  fontWeight="medium"
                  _hover={{ bg: isRunning ? "red.600" : "gray.800" }}
                  _disabled={{
                    bg: "gray.200",
                    color: "gray.400",
                    cursor: "not-allowed",
                  }}
                  px={4}
                >
                  {isRunning ? (
                    <Icon as={Square} boxSize={3.5} mr={2} />
                  ) : (
                    <Icon as={Play} boxSize={3.5} mr={2} />
                  )}
                  {isRunning ? "Stop" : "Run"}
                </Button>
              </>
            )}

            {/* Settings */}
            <IconButton
              onClick={onOpenRunConfig}
              aria-label="Settings"
              size="sm"
              variant="ghost"
              color="gray.500"
              _hover={{ color: "gray.900", bg: "gray.50" }}
            >
              <Icon as={Settings} boxSize={4} />
            </IconButton>
          </HStack>
        </Flex>
      </Box>

      <GroundTruthModal
        isOpen={showGroundTruthModal}
        onClose={() => setShowGroundTruthModal(false)}
        dataDir={dataDir || null}
        currentGroundTruthPath={groundTruthPath}
        onGroundTruthUpdated={(path, labelCount) => {
          if (onGroundTruthSelect) {
            onGroundTruthSelect(path, labelCount);
          }
          setShowGroundTruthModal(false);
        }}
      />
    </>
  );
});

import React, { useRef } from "react";
import {
  Box,
  Button,
  Badge,
  Heading,
  Text,
  VStack,
  HStack,
  Flex,
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { Upload } from "lucide-react";

// Motion components
const MotionFlex = motion(Flex);

interface UploadZoneProps {
  onFileSelect: (files: FileList) => void;
  hasUploads: boolean;
  isVisible: boolean;
  onToggleVisibility: (visible: boolean) => void;
  compact?: boolean;
}

const focusAreas = ["Site plans", "Floor plans", "Elevations", "Sections"];

export const UploadZone: React.FC<UploadZoneProps> = ({
  onFileSelect,
  hasUploads,
  isVisible,
  onToggleVisibility,
  compact = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [iconExiting, setIconExiting] = React.useState(false);

  // Detect when uploads start to trigger icon exit animation
  React.useEffect(() => {
    if (hasUploads && !iconExiting) {
      setIconExiting(true);
    }
  }, [hasUploads, iconExiting]);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      onFileSelect(files);
      // Reset input to allow selecting the same file again
      event.target.value = "";
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const files = event.dataTransfer.files;
    if (files && files.length > 0) {
      onFileSelect(files);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  if (!isVisible) {
    return null;
  }

  // Compact mode - minimal single-line version
  if (compact) {
    return (
      <Flex
        align="center"
        gap={3}
        borderRadius="xl"
        borderWidth="1px"
        borderStyle="dashed"
        borderColor="rgba(79, 134, 113, 0.28)"
        bg="rgba(236, 245, 240, 0.48)"
        px={{ base: 4, md: 5 }}
        py={{ base: 3, md: 3 }}
        transition="all 0.3s ease"
        _hover={{
          borderColor: "rgba(79, 134, 113, 0.42)",
          bg: "rgba(224, 238, 231, 0.58)",
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          multiple
          onChange={handleFileInput}
          style={{ display: "none" }}
          aria-hidden="true"
        />

        <Flex
          align="center"
          justify="center"
          w={10}
          h={10}
          borderRadius="full"
          bg="rgba(79, 134, 113, 0.16)"
          flexShrink={0}
        >
          <Upload size={20} color="var(--chakra-colors-brand-600)" />
        </Flex>

        <VStack align="flex-start" gap={0} flex="1" minW={0}>
          <Text fontSize="sm" fontWeight="600" color="fg.emphasis">
            Upload more drawings
          </Text>
          <Text fontSize="xs" color="fg.muted" lineClamp={1}>
            PDF, PNG or JPG • Drag and drop or click to browse
          </Text>
        </VStack>

        <HStack gap={2}>
          <Button
            size="sm"
            variant="solid"
            onClick={(e) => {
              e.stopPropagation();
              handleClick();
            }}
            minH="40px"
          >
            Browse
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={(e) => {
              e.stopPropagation();
              onToggleVisibility(false);
            }}
            minH="40px"
          >
            Hide
          </Button>
        </HStack>
      </Flex>
    );
  }

  // Full mode - large prominent version
  return (
    <Box
      borderRadius="2xl"
      borderWidth="1px"
      borderStyle="dashed"
      borderColor={
        hasUploads ? "rgba(79, 134, 113, 0.42)" : "rgba(79, 134, 113, 0.28)"
      }
      bg={
        hasUploads ? "rgba(224, 238, 231, 0.58)" : "rgba(236, 245, 240, 0.68)"
      }
      px={{ base: 6, md: 8 }}
      py={{ base: 8, md: 10 }}
      transition="all 0.3s ease"
      cursor="pointer"
      onClick={handleClick}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      _hover={{
        borderColor: "rgba(79, 134, 113, 0.52)",
        bg: "rgba(224, 238, 231, 0.72)",
        transform: "translateY(-2px)",
      }}
      role="button"
      aria-label="Upload planning drawings"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          handleClick();
        }
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        multiple
        onChange={handleFileInput}
        style={{ display: "none" }}
        aria-hidden="true"
      />
      <VStack gap={5} align="center" textAlign="center">
        <MotionFlex
          align="center"
          justify="center"
          w={{ base: 16, md: 20 }}
          h={{ base: 16, md: 20 }}
          borderRadius="full"
          bg="rgba(79, 134, 113, 0.22)"
          animate={{
            scale: iconExiting ? 0.7 : 1,
            opacity: iconExiting ? 0 : 1,
          }}
          transition={{
            duration: 0.3,
            ease: "easeOut",
          }}
        >
          <Upload size={40} color="var(--chakra-colors-brand-600)" />
        </MotionFlex>
        <Heading size={{ base: "md", md: "lg" }}>
          {hasUploads ? "Add more drawings" : "Drop your planning drawings"}
        </Heading>
        <Text fontSize={{ base: "sm", md: "md" }} color="fg.muted" maxW="lg">
          {hasUploads
            ? "Upload additional files to validate alongside your existing drawings."
            : "PDF, PNG or JPG • Upload multiple files at once • Instant validation"}
        </Text>
        <Button
          variant="solid"
          size={{ base: "md", md: "lg" }}
          minH={{ base: "44px", md: "48px" }}
          px={{ base: 6, md: 8 }}
          onClick={(e) => {
            e.stopPropagation();
            handleClick();
          }}
        >
          Browse files
        </Button>
        <HStack gap={3} flexWrap="wrap" justify="center">
          {focusAreas.map((area) => (
            <Badge
              key={area}
              borderRadius="full"
              px={4}
              py={1.5}
              fontSize={{ base: "xs", md: "sm" }}
              bg="rgba(79, 134, 113, 0.12)"
              color="brand.700"
            >
              {area}
            </Badge>
          ))}
        </HStack>
        {hasUploads && (
          <Button
            variant="ghost"
            size="sm"
            minH="44px"
            color="fg.muted"
            onClick={(e) => {
              e.stopPropagation();
              onToggleVisibility(false);
            }}
          >
            Hide upload area
          </Button>
        )}
      </VStack>
    </Box>
  );
};

/**
 * DocumentUpload Component
 *
 * Main upload interface with drag-and-drop support, real-time validation,
 * and detailed results display. Includes mobile-first responsive design
 * and WCAG AA accessibility.
 */

import React, { useState } from "react";
import { VStack, Flex, Heading, Text, Badge, Box } from "@chakra-ui/react";
import { motion, AnimatePresence } from "framer-motion";
import { DocumentUpload as DocumentUploadType } from "../types";
import {
  UploadZone,
  UploadGrid,
  UploadDetail,
  FloatingUploadButton,
} from "./DocumentUpload/index";

// Motion components
const MotionBox = motion(Box);

interface Props {
  onFileSelect: (files: FileList) => void;
  uploads: DocumentUploadType[];
}

export const DocumentUpload: React.FC<Props> = ({ onFileSelect, uploads }) => {
  const [selectedUploadId, setSelectedUploadId] = useState<string | null>(null);

  const hasUploads = uploads.length > 0;

  // Auto-select first upload if none selected
  React.useEffect(() => {
    if (uploads.length > 0 && !selectedUploadId) {
      setSelectedUploadId(uploads[0].id);
    }
  }, [uploads.length, selectedUploadId]);

  // Find selected upload
  const selectedUpload = uploads.find((u) => u.id === selectedUploadId);

  // Sort uploads: processing first, then completed, then errors
  const orderedUploads = [...uploads].sort((a, b) => {
    const statusOrder = {
      uploading: 0,
      validating: 1,
      complete: 2,
      error: 3,
    };
    return statusOrder[a.status.status] - statusOrder[b.status.status];
  });

  // Count uploads by status
  const processingCount = uploads.filter(
    (u) => u.status.status === "uploading" || u.status.status === "validating",
  ).length;
  const completeCount = uploads.filter(
    (u) => u.status.status === "complete",
  ).length;

  // Handle preview
  const handlePreview = (upload: DocumentUploadType) => {
    const url = URL.createObjectURL(upload.file);
    window.open(url, "_blank");
    // Clean up URL after a delay
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  };

  return (
    <>
      {/* Upload zone - animated transition when first upload happens */}
      <AnimatePresence mode="wait">
        {!hasUploads && (
          <MotionBox
            key="upload-zone"
            initial={{ opacity: 1, scale: 1, y: 0 }}
            exit={{
              opacity: 0,
              scale: 0.95,
              y: -20,
              transition: { duration: 0.3, ease: "easeInOut" },
            }}
          >
            <VStack gap={{ base: 6, md: 7 }} align="stretch">
              <UploadZone
                onFileSelect={onFileSelect}
                hasUploads={hasUploads}
                isVisible={true}
                onToggleVisibility={() => {}}
                compact={false}
              />
            </VStack>
          </MotionBox>
        )}
      </AnimatePresence>

      {/* Floating upload button - animated journey from upload icon to bottom-right */}
      <AnimatePresence>
        {hasUploads && (
          <MotionBox
            key="floating-button"
            style={{ position: "fixed", zIndex: 1001 }}
            initial={{
              top: "90px", // Start at upload icon position (page padding + upload zone padding + icon offset)
              left: "50%",
              x: "-50%", // Center horizontally at icon
              bottom: "auto",
              right: "auto",
              opacity: 0,
              scale: 0.8, // Start smaller to match icon size
            }}
            animate={{
              top: "auto",
              bottom: "24px", // Final position
              right: "24px",
              left: "auto",
              x: 0,
              opacity: 1,
              scale: 1,
              transition: {
                duration: 0.7,
                ease: [0.34, 1.56, 0.64, 1], // Bouncy ease for playful feel
                delay: 0.1,
              },
            }}
            exit={{
              opacity: 0,
              scale: 0.5,
              transition: { duration: 0.2 },
            }}
          >
            <FloatingUploadButton onFileSelect={onFileSelect} />
          </MotionBox>
        )}
      </AnimatePresence>

      {/* Uploads section - animated entrance */}
      <AnimatePresence>
        {orderedUploads.length > 0 && (
          <MotionBox
            key="uploads-section"
            initial={{ opacity: 0, y: 20 }}
            animate={{
              opacity: 1,
              y: 0,
              transition: {
                duration: 0.4,
                ease: "easeOut",
                delay: 0.3, // Appear after upload zone exits
              },
            }}
          >
            <VStack as="section" gap={{ base: 6, md: 7 }} align="stretch">
              <VStack align="stretch" gap={{ base: 6, md: 8 }}>
                {/* Section header */}
                <Flex
                  justify="space-between"
                  align={{ base: "flex-start", md: "center" }}
                  wrap="wrap"
                  gap={4}
                >
                  <VStack align="flex-start" gap={2}>
                    <Heading
                      as="h2"
                      fontSize={{ base: "lg", md: "xl" }}
                      fontWeight="600"
                      letterSpacing="-0.02em"
                      color="fg.emphasis"
                    >
                      My Drawings
                    </Heading>
                    <Text
                      fontSize={{ base: "sm", md: "md" }}
                      color="fg.muted"
                      maxW="32rem"
                    >
                      Review validation results for all uploaded planning
                      drawings
                    </Text>
                    <Badge
                      px={3}
                      py={1}
                      borderRadius="full"
                      fontSize="xs"
                      letterSpacing="0.02em"
                      bg="rgba(79, 134, 113, 0.16)"
                      color="brand.700"
                    >
                      {processingCount} analysing • {completeCount} complete
                    </Badge>
                  </VStack>
                </Flex>

                {/* Upload grid */}
                <UploadGrid
                  uploads={orderedUploads}
                  selectedUploadId={selectedUploadId}
                  onSelectUpload={setSelectedUploadId}
                />

                {/* Detail panel for selected upload */}
                {selectedUpload && (
                  <UploadDetail
                    upload={selectedUpload}
                    onPreview={handlePreview}
                  />
                )}
              </VStack>
            </VStack>
          </MotionBox>
        )}
      </AnimatePresence>
    </>
  );
};

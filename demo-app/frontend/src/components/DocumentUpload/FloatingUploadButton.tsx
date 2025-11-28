import React, { useState } from "react";
import {
  IconButton,
  Drawer,
  VStack,
  Text,
  Box,
  CloseButton,
} from "@chakra-ui/react";
import { Upload } from "lucide-react";

interface FloatingUploadButtonProps {
  onFileSelect: (files: FileList) => void;
}

/**
 * FloatingUploadButton - Floating action button for uploading more documents
 *
 * Appears in bottom-right corner when uploads exist, opens a drawer with upload zone.
 * Follows mobile-first design with drawer sliding from bottom on mobile, right on desktop.
 */
export const FloatingUploadButton: React.FC<FloatingUploadButtonProps> = ({
  onFileSelect,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const onOpen = () => setIsOpen(true);
  const onClose = () => setIsOpen(false);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      onFileSelect(files);
      onClose();
    }
    // Reset input so same file can be selected again
    event.target.value = "";
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf,image/png,image/jpeg"
        multiple
        style={{ display: "none" }}
        onChange={handleFileChange}
      />

      {/* Floating Action Button */}
      <IconButton
        aria-label="Upload more documents"
        onClick={onOpen}
        size="lg"
        colorPalette="brand"
        borderRadius="full"
        boxShadow="0 4px 20px rgba(79, 134, 113, 0.3)"
        width="64px"
        height="64px"
        zIndex={1000}
        _hover={{
          transform: "scale(1.05)",
          boxShadow: "0 6px 24px rgba(79, 134, 113, 0.4)",
        }}
        transition="all 0.2s"
      >
        <Upload size={24} />
      </IconButton>

      {/* Upload Drawer */}
      <Drawer.Root
        open={isOpen}
        onOpenChange={(e) => setIsOpen(e.open)}
        placement="end"
      >
        <Drawer.Backdrop />
        <Drawer.Positioner>
          <Drawer.Content>
            <Drawer.Header
              borderBottomWidth="1px"
              borderBottomColor="rgba(79, 134, 113, 0.2)"
            >
              <Drawer.Title>Upload Documents</Drawer.Title>
              <Drawer.CloseTrigger asChild>
                <CloseButton size="sm" />
              </Drawer.CloseTrigger>
            </Drawer.Header>

            <Drawer.Body py={6}>
              <VStack align="stretch" gap={6}>
                {/* Upload zone */}
                <Box
                  borderRadius="2xl"
                  borderWidth="2px"
                  borderStyle="dashed"
                  borderColor="rgba(79, 134, 113, 0.28)"
                  bg="rgba(236, 245, 240, 0.48)"
                  p={{ base: 8, md: 10 }}
                  textAlign="center"
                  cursor="pointer"
                  transition="all 0.2s"
                  onClick={handleBrowseClick}
                  onDragOver={(e) => {
                    e.preventDefault();
                    e.currentTarget.style.borderColor =
                      "rgba(79, 134, 113, 0.6)";
                    e.currentTarget.style.backgroundColor =
                      "rgba(236, 245, 240, 0.8)";
                  }}
                  onDragLeave={(e) => {
                    e.currentTarget.style.borderColor =
                      "rgba(79, 134, 113, 0.28)";
                    e.currentTarget.style.backgroundColor =
                      "rgba(236, 245, 240, 0.48)";
                  }}
                  onDrop={(e) => {
                    e.preventDefault();
                    e.currentTarget.style.borderColor =
                      "rgba(79, 134, 113, 0.28)";
                    e.currentTarget.style.backgroundColor =
                      "rgba(236, 245, 240, 0.48)";
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                      onFileSelect(files);
                      onClose();
                    }
                  }}
                  _hover={{
                    borderColor: "rgba(79, 134, 113, 0.4)",
                    bg: "rgba(236, 245, 240, 0.64)",
                  }}
                >
                  <VStack gap={4}>
                    <Upload size={48} color="var(--chakra-colors-brand-600)" />
                    <VStack gap={2}>
                      <Text
                        fontSize={{ base: "lg", md: "xl" }}
                        fontWeight="600"
                        color="fg.emphasis"
                      >
                        Drop files here or click to browse
                      </Text>
                      <Text
                        fontSize={{ base: "sm", md: "md" }}
                        color="fg.muted"
                        maxW="400px"
                      >
                        Upload planning drawings for validation. Supports PDF,
                        PNG, and JPG formats.
                      </Text>
                    </VStack>
                  </VStack>
                </Box>

                {/* Supported formats */}
                <Box bg="rgba(79, 134, 113, 0.08)" borderRadius="lg" p={4}>
                  <Text
                    fontSize="sm"
                    fontWeight="600"
                    color="fg.emphasis"
                    mb={2}
                  >
                    Supported formats
                  </Text>
                  <Text fontSize="sm" color="fg.muted">
                    PDF, PNG, JPG • Multiple files • Max 10MB per file
                  </Text>
                </Box>
              </VStack>
            </Drawer.Body>
          </Drawer.Content>
        </Drawer.Positioner>
      </Drawer.Root>
    </>
  );
};

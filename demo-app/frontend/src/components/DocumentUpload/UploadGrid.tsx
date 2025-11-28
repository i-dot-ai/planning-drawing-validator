import React, { useRef, useCallback } from "react";
import { SimpleGrid, VStack, useBreakpointValue } from "@chakra-ui/react";
import { DocumentUpload as DocumentUploadType } from "../../types";
import { UploadCard } from "./UploadCard";

interface UploadGridProps {
  uploads: DocumentUploadType[];
  selectedUploadId: string | null;
  onSelectUpload: (id: string) => void;
}

export const UploadGrid: React.FC<UploadGridProps> = ({
  uploads,
  selectedUploadId,
  onSelectUpload,
}) => {
  const cardRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const isMobile = useBreakpointValue({ base: true, md: false });

  const registerCardRef = useCallback(
    (uploadId: string) => (element: HTMLDivElement | null) => {
      cardRefs.current[uploadId] = element;
    },
    [],
  );

  const handleCardClick = (uploadId: string) => {
    onSelectUpload(uploadId);
    cardRefs.current[uploadId]?.focus();
  };

  const handleKeyDown = (
    event: React.KeyboardEvent,
    upload: DocumentUploadType,
    index: number,
  ) => {
    const currentIndex = index;
    const totalUploads = uploads.length;

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelectUpload(upload.id);
      return;
    }

    // Navigation keys
    let nextIndex = -1;

    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      nextIndex = currentIndex + 1;
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      nextIndex = currentIndex - 1;
    }

    // Wrap around navigation
    if (nextIndex >= 0 && nextIndex < totalUploads) {
      const nextUpload = uploads[nextIndex];
      onSelectUpload(nextUpload.id);
      cardRefs.current[nextUpload.id]?.focus();
    }
  };

  // Mobile: vertical stack, Desktop: responsive grid
  if (isMobile) {
    return (
      <VStack gap={4} align="stretch">
        {uploads.map((upload, index) => (
          <UploadCard
            key={upload.id}
            upload={upload}
            isActive={selectedUploadId === upload.id}
            onClick={() => handleCardClick(upload.id)}
            onKeyDown={(event) => handleKeyDown(event, upload, index)}
            cardRef={registerCardRef(upload.id)}
          />
        ))}
      </VStack>
    );
  }

  // Desktop: responsive grid (2-3 columns based on space)
  return (
    <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={6} w="100%">
      {uploads.map((upload, index) => (
        <UploadCard
          key={upload.id}
          upload={upload}
          isActive={selectedUploadId === upload.id}
          onClick={() => handleCardClick(upload.id)}
          onKeyDown={(event) => handleKeyDown(event, upload, index)}
          cardRef={registerCardRef(upload.id)}
        />
      ))}
    </SimpleGrid>
  );
};

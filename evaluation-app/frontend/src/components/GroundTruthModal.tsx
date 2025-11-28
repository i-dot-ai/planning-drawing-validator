import React, { useState, useEffect } from "react";
import {
  Button,
  Box,
  Flex,
  Text,
  VStack,
  HStack,
  NativeSelect,
  Input,
  Icon,
  Spinner,
  Dialog,
  Portal,
  CloseButton,
} from "@chakra-ui/react";
import { toast } from "sonner";
import { Trash2, FileSpreadsheet } from "lucide-react";
import { api, APIError } from "@/lib/api";

interface GroundTruthEntry {
  document_id: string;
  filename: string;
  expected_validity: string;
}

interface GroundTruthModalProps {
  isOpen: boolean;
  onClose: () => void;
  dataDir: string | null;
  currentGroundTruthPath?: string;
  onGroundTruthUpdated: (path: string, labelCount: number) => void;
}

export const GroundTruthModal: React.FC<GroundTruthModalProps> = ({
  isOpen,
  onClose,
  dataDir,
  currentGroundTruthPath,
  onGroundTruthUpdated,
}) => {
  const [availableDocuments, setAvailableDocuments] = useState<any[]>([]);
  const [groundTruthEntries, setGroundTruthEntries] = useState<
    GroundTruthEntry[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isOpen && dataDir) {
      loadAvailableDocuments();
      if (currentGroundTruthPath) {
        loadExistingGroundTruth();
      }
    }
  }, [isOpen, dataDir, currentGroundTruthPath]);

  const loadAvailableDocuments = async () => {
    if (!dataDir) return;
    setLoading(true);
    try {
      const data = await api.documents.getDocuments();
      setAvailableDocuments(data.documents);
    } catch (error) {
      console.error("Failed to load documents:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadExistingGroundTruth = async () => {
    if (!currentGroundTruthPath) return;
    try {
      const data = await api.groundTruth.getGroundTruth(currentGroundTruthPath);
      if (data.entries) {
        setGroundTruthEntries(data.entries);
      }
    } catch (error) {
      console.error("Failed to load existing ground truth:", error);
    }
  };

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    try {
      const data = await api.groundTruth.uploadGroundTruth(file);
      if (data.ground_truth_path) {
        const labelCount = data.entries_count || 0;
        onGroundTruthUpdated(data.ground_truth_path, labelCount);
        onClose();
      }
    } catch (error) {
      const message =
        error instanceof APIError
          ? error.detail || error.message
          : "Upload failed";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const addEntry = (documentId: string, filename: string) => {
    if (groundTruthEntries.some((e) => e.document_id === documentId)) return;
    setGroundTruthEntries([
      ...groundTruthEntries,
      { document_id: documentId, filename, expected_validity: "VALID" },
    ]);
  };

  const removeEntry = (documentId: string) => {
    setGroundTruthEntries(
      groundTruthEntries.filter((e) => e.document_id !== documentId),
    );
  };

  const updateEntry = (documentId: string, expectedValidity: string) => {
    setGroundTruthEntries(
      groundTruthEntries.map((e) =>
        e.document_id === documentId
          ? { ...e, expected_validity: expectedValidity }
          : e,
      ),
    );
  };

  const saveGroundTruth = async () => {
    if (groundTruthEntries.length === 0 || !dataDir) return;

    setSaving(true);
    try {
      const data = await api.groundTruth.saveGroundTruth(
        dataDir,
        groundTruthEntries,
      );
      if (data.ground_truth_path) {
        onGroundTruthUpdated(data.ground_truth_path, groundTruthEntries.length);
        onClose();
      }
    } catch (error) {
      const message =
        error instanceof APIError
          ? error.detail || error.message
          : "Save failed";
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog.Root
      open={isOpen}
      onOpenChange={(details: { open: boolean }) => !details.open && onClose()}
      size="lg"
    >
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content borderRadius="xl" mx={4}>
            <Dialog.Header pb={0} pt={5} px={5}>
              <Text fontSize="lg" fontWeight="semibold" color="gray.900">
                Labels
              </Text>
              <Text fontSize="sm" color="gray.500" fontWeight="normal" mt={0.5}>
                Upload a file or label documents manually
              </Text>
            </Dialog.Header>
            <Box position="absolute" top={4} right={4}>
              <Dialog.CloseTrigger asChild>
                <CloseButton size="sm" />
              </Dialog.CloseTrigger>
            </Box>

            <Dialog.Body px={5} py={5}>
              <VStack gap={4} align="stretch">
                {/* Upload Section */}
                <Flex
                  align="center"
                  justify="space-between"
                  p={3}
                  bg="gray.50"
                  borderRadius="lg"
                  border="1px"
                  borderColor="gray.200"
                >
                  <HStack gap={3}>
                    <Box
                      p={2}
                      bg="white"
                      borderRadius="md"
                      border="1px"
                      borderColor="gray.200"
                    >
                      <Icon as={FileSpreadsheet} boxSize={5} color="gray.500" />
                    </Box>
                    <Box>
                      <Text fontSize="sm" fontWeight="medium" color="gray.700">
                        Import from file
                      </Text>
                      <Text fontSize="xs" color="gray.500">
                        JSON, YAML, or Excel
                      </Text>
                    </Box>
                  </HStack>
                  <Button
                    as="label"
                    size="sm"
                    variant="outline"
                    cursor="pointer"
                    loading={loading}
                    fontWeight="medium"
                  >
                    Choose file
                    <Input
                      type="file"
                      accept=".json,.yaml,.yml,.xlsx"
                      onChange={handleFileUpload}
                      disabled={loading}
                      display="none"
                    />
                  </Button>
                </Flex>

                {/* Divider */}
                <Flex align="center" gap={3}>
                  <Box flex={1} h="1px" bg="gray.200" />
                  <Text fontSize="xs" color="gray.400" fontWeight="medium">
                    OR
                  </Text>
                  <Box flex={1} h="1px" bg="gray.200" />
                </Flex>

                {/* Manual Labeling */}
                <Box>
                  <Text
                    fontSize="sm"
                    fontWeight="medium"
                    color="gray.700"
                    mb={2}
                  >
                    Label manually
                  </Text>

                  {loading ? (
                    <Flex justify="center" py={6}>
                      <Spinner size="sm" color="gray.400" />
                    </Flex>
                  ) : availableDocuments.length === 0 ? (
                    <Text
                      fontSize="sm"
                      color="gray.500"
                      py={4}
                      textAlign="center"
                    >
                      Upload documents first
                    </Text>
                  ) : (
                    <Box
                      maxH="200px"
                      overflowY="auto"
                      border="1px"
                      borderColor="gray.200"
                      borderRadius="lg"
                    >
                      {availableDocuments.map((doc, index) => {
                        const entry = groundTruthEntries.find(
                          (e) => e.document_id === doc.document_id,
                        );
                        const isLabeled = !!entry;

                        return (
                          <Flex
                            key={doc.document_id}
                            align="center"
                            justify="space-between"
                            px={3}
                            py={2}
                            borderBottom={
                              index < availableDocuments.length - 1
                                ? "1px"
                                : "none"
                            }
                            borderColor="gray.100"
                            bg={isLabeled ? "blue.50" : "white"}
                            _hover={{ bg: isLabeled ? "blue.50" : "gray.50" }}
                          >
                            <Text
                              fontSize="sm"
                              color="gray.700"
                              lineClamp={1}
                              flex={1}
                              mr={3}
                            >
                              {doc.filename}
                            </Text>

                            {isLabeled ? (
                              <HStack gap={2}>
                                <NativeSelect.Root size="xs" w="110px">
                                  <NativeSelect.Field
                                    value={entry.expected_validity}
                                    onChange={(e) =>
                                      updateEntry(
                                        doc.document_id,
                                        e.target.value,
                                      )
                                    }
                                  >
                                    <option value="VALID">Valid</option>
                                    <option value="INVALID">Invalid</option>
                                  </NativeSelect.Field>
                                </NativeSelect.Root>
                                <Button
                                  size="xs"
                                  variant="ghost"
                                  color="gray.400"
                                  onClick={() => removeEntry(doc.document_id)}
                                  minW="auto"
                                  px={1}
                                  _hover={{ color: "red.500" }}
                                >
                                  <Icon as={Trash2} boxSize={3.5} />
                                </Button>
                              </HStack>
                            ) : (
                              <Button
                                size="xs"
                                variant="ghost"
                                color="gray.500"
                                fontWeight="medium"
                                onClick={() =>
                                  addEntry(doc.document_id, doc.filename)
                                }
                                _hover={{ color: "gray.900", bg: "gray.100" }}
                              >
                                Add
                              </Button>
                            )}
                          </Flex>
                        );
                      })}
                    </Box>
                  )}
                </Box>

                {/* Footer Actions */}
                {groundTruthEntries.length > 0 && (
                  <Flex justify="space-between" align="center" pt={2}>
                    <Text fontSize="sm" color="gray.500">
                      {groundTruthEntries.length} labeled
                    </Text>
                    <HStack gap={2}>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={onClose}
                        fontWeight="medium"
                      >
                        Cancel
                      </Button>
                      <Button
                        size="sm"
                        bg="gray.900"
                        color="white"
                        onClick={saveGroundTruth}
                        loading={saving}
                        fontWeight="medium"
                        _hover={{ bg: "gray.800" }}
                      >
                        Save
                      </Button>
                    </HStack>
                  </Flex>
                )}
              </VStack>
            </Dialog.Body>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  );
};

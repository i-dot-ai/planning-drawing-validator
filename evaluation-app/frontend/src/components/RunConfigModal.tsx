import React, { useState, useEffect } from "react";
import {
  FileText,
  Filter,
  ChevronDown,
  ChevronRight,
  Table,
} from "lucide-react";
import {
  Button,
  Input,
  VStack,
  HStack,
  Box,
  Checkbox,
  Text,
  Icon,
  NativeSelect,
  Separator,
  Field,
  Collapsible,
  Dialog,
  Portal,
  CloseButton,
} from "@chakra-ui/react";
import { DocumentInfo, ModelInfo } from "../types";

export type ReasoningEffort = "none" | "low" | "medium" | "high" | null;

export interface ColumnConfig {
  filename: string | null;
  validity: string | null;
  reason: string | null;
}

export interface RunConfig {
  maxSamples: number | null;
  concurrency: number;
  documentIds: string[];
  modelName: string;
  reasoningEffort: ReasoningEffort;
  columnConfig: ColumnConfig | null;
}

interface RunConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (config: RunConfig) => void;
  currentConfig: RunConfig;
  availableDocuments: DocumentInfo[];
}

export const RunConfigModal: React.FC<RunConfigModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  currentConfig,
  availableDocuments,
}) => {
  const [config, setConfig] = useState<RunConfig>(currentConfig);
  const [filterMode, setFilterMode] = useState<"all" | "selected">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [concurrencyInput, setConcurrencyInput] = useState(
    String(currentConfig.concurrency),
  );

  useEffect(() => {
    if (isOpen) {
      setConfig(currentConfig);
      setFilterMode(currentConfig.documentIds.length > 0 ? "selected" : "all");
      setConcurrencyInput(String(currentConfig.concurrency));
    }
  }, [currentConfig, isOpen]);

  useEffect(() => {
    if (isOpen) {
      fetch("/api/models")
        .then((res) => res.json())
        .then((data: { models: ModelInfo[] }) => {
          setAvailableModels(data.models);
          if (!config.modelName) {
            const defaultModel = data.models.find((m) => m.is_default);
            if (defaultModel) {
              setConfig((prev) => ({ ...prev, modelName: defaultModel.id }));
            }
          }
        })
        .catch((err) => console.error("Failed to fetch models:", err));
    }
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsedConcurrency = parseInt(concurrencyInput, 10);
    const validConcurrency =
      isNaN(parsedConcurrency) || parsedConcurrency < 1 ? 1 : parsedConcurrency;
    const finalConfig = {
      ...config,
      concurrency: validConcurrency,
      documentIds: filterMode === "all" ? [] : config.documentIds,
    };
    onSubmit(finalConfig);
    onClose();
  };

  const toggleDocument = (docId: string) => {
    setConfig((prev) => ({
      ...prev,
      documentIds: prev.documentIds.includes(docId)
        ? prev.documentIds.filter((id) => id !== docId)
        : [...prev.documentIds, docId],
    }));
  };

  const filteredDocuments = availableDocuments.filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <Dialog.Root
      open={isOpen}
      onOpenChange={(details: { open: boolean }) => !details.open && onClose()}
      size="xl"
    >
      <Portal>
        <Dialog.Backdrop />
        <Dialog.Positioner>
          <Dialog.Content
            borderRadius="xl"
            maxH="90vh"
            bg="white"
            borderWidth="1px"
            borderColor="gray.200"
            boxShadow="lg"
            display="flex"
            flexDirection="column"
          >
            <Dialog.Header
              borderBottomWidth="1px"
              borderColor="gray.200"
              pb={3}
              pt={4}
              px={6}
              flexShrink={0}
            >
              <Text fontSize="md" fontWeight="semibold" color="fg.emphasis">
                Run Configuration
              </Text>
            </Dialog.Header>
            <Box position="absolute" top={4} right={4}>
              <Dialog.CloseTrigger asChild>
                <CloseButton
                  size="sm"
                  borderRadius="xl"
                  _hover={{ bg: "gray.100" }}
                />
              </Dialog.CloseTrigger>
            </Box>

            <form
              onSubmit={handleSubmit}
              style={{
                display: "flex",
                flexDirection: "column",
                flex: 1,
                minHeight: 0,
              }}
            >
              <Dialog.Body px={6} py={4} flex={1} overflowY="auto">
                <VStack gap={4} align="stretch">
                  {/* Model Selection */}
                  <Field.Root>
                    <Field.Label
                      fontSize="sm"
                      fontWeight="medium"
                      color="gray.700"
                    >
                      Model ({availableModels.length} available)
                    </Field.Label>
                    <NativeSelect.Root size="sm">
                      <NativeSelect.Field
                        value={config.modelName}
                        onChange={(e) =>
                          setConfig({ ...config, modelName: e.target.value })
                        }
                        placeholder="Select a model"
                      >
                        {availableModels.map((model) => (
                          <option key={model.id} value={model.id}>
                            {model.display_name}
                          </option>
                        ))}
                      </NativeSelect.Field>
                    </NativeSelect.Root>
                    <Field.HelperText fontSize="xs" color="fg.muted">
                      {(() => {
                        const selectedModel = availableModels.find(
                          (m) => m.id === config.modelName,
                        );
                        if (selectedModel) {
                          const parts = [
                            selectedModel.provider || "Unknown provider",
                          ];
                          if (selectedModel.reasoning_effort) {
                            parts.push(
                              `reasoning: ${selectedModel.reasoning_effort}`,
                            );
                          }
                          return parts.join(" • ");
                        }
                        return "Select a model to see details";
                      })()}
                    </Field.HelperText>
                  </Field.Root>

                  {/* Reasoning Effort */}
                  <Field.Root>
                    <Field.Label
                      fontSize="sm"
                      fontWeight="medium"
                      color="gray.700"
                    >
                      Reasoning Effort
                    </Field.Label>
                    <NativeSelect.Root size="sm">
                      <NativeSelect.Field
                        value={config.reasoningEffort ?? ""}
                        onChange={(e) => {
                          const value = e.target.value;
                          setConfig({
                            ...config,
                            reasoningEffort:
                              value === "" ? null : (value as ReasoningEffort),
                          });
                        }}
                      >
                        <option value="">Use model default</option>
                        <option value="none">None (disabled)</option>
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </NativeSelect.Field>
                    </NativeSelect.Root>
                    <Field.HelperText fontSize="xs" color="fg.muted">
                      {(() => {
                        const selectedModel = availableModels.find(
                          (m) => m.id === config.modelName,
                        );
                        const modelDefault = selectedModel?.reasoning_effort;
                        if (config.reasoningEffort) {
                          return `Override: ${config.reasoningEffort} (model default: ${modelDefault || "none"})`;
                        }
                        return `Using model default: ${modelDefault || "none"}`;
                      })()}
                    </Field.HelperText>
                  </Field.Root>

                  {/* Concurrency */}
                  <Field.Root>
                    <Field.Label
                      fontSize="sm"
                      fontWeight="medium"
                      color="gray.700"
                    >
                      Concurrency
                    </Field.Label>
                    <Input
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      value={concurrencyInput}
                      onChange={(e) => {
                        const value = e.target.value;
                        if (value === "" || /^\d+$/.test(value)) {
                          setConcurrencyInput(value);
                        }
                      }}
                      onBlur={() => {
                        const parsed = parseInt(concurrencyInput, 10);
                        const validValue =
                          isNaN(parsed) || parsed < 1 ? 1 : parsed;
                        setConcurrencyInput(String(validValue));
                        setConfig({ ...config, concurrency: validValue });
                      }}
                      borderRadius="sm"
                      borderWidth="1px"
                      borderColor="gray.200"
                      fontSize="sm"
                      _hover={{ borderColor: "gray.300" }}
                      _focus={{
                        borderColor: "gray.900",
                        boxShadow: "0 0 0 1px rgba(0, 0, 0, 0.1)",
                      }}
                    />
                    <Field.HelperText fontSize="xs" color="fg.muted">
                      Number of documents to process simultaneously (minimum 1)
                    </Field.HelperText>
                  </Field.Root>

                  {/* Max Samples */}
                  <Field.Root>
                    <Field.Label
                      fontSize="sm"
                      fontWeight="medium"
                      color="gray.700"
                    >
                      Maximum Samples
                    </Field.Label>
                    <Input
                      type="number"
                      min={0}
                      value={config.maxSamples || ""}
                      onChange={(e) =>
                        setConfig({
                          ...config,
                          maxSamples: e.target.value
                            ? parseInt(e.target.value, 10)
                            : null,
                        })
                      }
                      placeholder="All documents"
                      borderRadius="sm"
                      borderWidth="1px"
                      borderColor="gray.200"
                      fontSize="sm"
                      _hover={{ borderColor: "gray.300" }}
                      _focus={{
                        borderColor: "gray.900",
                        boxShadow: "0 0 0 1px rgba(0, 0, 0, 0.1)",
                      }}
                      _placeholder={{ color: "gray.400" }}
                    />
                    <Field.HelperText fontSize="xs" color="fg.muted">
                      Limit the number of documents to evaluate (leave empty for
                      all)
                    </Field.HelperText>
                  </Field.Root>

                  {/* Document Filter */}
                  <Field.Root>
                    <Field.Label
                      fontSize="sm"
                      fontWeight="medium"
                      color="gray.700"
                      display="flex"
                      alignItems="center"
                      gap={2}
                    >
                      <Icon as={Filter} boxSize={4} />
                      Document Filter
                    </Field.Label>

                    {/* Filter Mode Tabs */}
                    <HStack
                      gap={0}
                      p={0.5}
                      borderRadius="sm"
                      borderWidth="1px"
                      borderColor="gray.200"
                      bg="white"
                      mb={3}
                    >
                      <Button
                        onClick={() => setFilterMode("all")}
                        flex={1}
                        size="sm"
                        fontSize="xs"
                        fontWeight="medium"
                        borderRadius="sm"
                        bg={filterMode === "all" ? "gray.900" : "transparent"}
                        color={filterMode === "all" ? "white" : "gray.600"}
                        _hover={{
                          bg: filterMode === "all" ? "gray.800" : "gray.100",
                          color: filterMode === "all" ? "white" : "gray.900",
                        }}
                      >
                        All Documents
                      </Button>
                      <Button
                        onClick={() => setFilterMode("selected")}
                        flex={1}
                        size="sm"
                        fontSize="xs"
                        fontWeight="medium"
                        borderRadius="sm"
                        bg={
                          filterMode === "selected" ? "gray.900" : "transparent"
                        }
                        color={filterMode === "selected" ? "white" : "gray.600"}
                        _hover={{
                          bg:
                            filterMode === "selected" ? "gray.800" : "gray.100",
                          color:
                            filterMode === "selected" ? "white" : "gray.900",
                        }}
                      >
                        Selected ({config.documentIds.length})
                      </Button>
                    </HStack>

                    {filterMode === "selected" && (
                      <VStack gap={3} align="stretch">
                        {/* Search */}
                        <Box position="relative">
                          <Box
                            position="absolute"
                            left={3}
                            top="50%"
                            transform="translateY(-50%)"
                            pointerEvents="none"
                          >
                            <Icon as={Filter} boxSize={4} color="gray.400" />
                          </Box>
                          <Input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search documents..."
                            borderRadius="sm"
                            borderWidth="1px"
                            borderColor="gray.200"
                            fontSize="sm"
                            pl={10}
                            _hover={{ borderColor: "gray.300" }}
                            _focus={{
                              borderColor: "gray.900",
                              boxShadow: "0 0 0 1px rgba(0, 0, 0, 0.1)",
                            }}
                            _placeholder={{ color: "gray.400" }}
                          />
                        </Box>

                        {/* Document List */}
                        <Box
                          maxH="40"
                          overflowY="auto"
                          borderRadius="sm"
                          borderWidth="1px"
                          borderColor="gray.200"
                        >
                          {filteredDocuments.length === 0 ? (
                            <Box px={4} py={8} textAlign="center">
                              <Text fontSize="sm" color="fg.muted">
                                No documents found
                              </Text>
                            </Box>
                          ) : (
                            <VStack
                              gap={0}
                              align="stretch"
                              separator={<Separator />}
                            >
                              {filteredDocuments.map((doc) => (
                                <Box
                                  key={doc.filename}
                                  as="label"
                                  display="flex"
                                  alignItems="center"
                                  gap={3}
                                  px={4}
                                  py={2.5}
                                  cursor="pointer"
                                  _hover={{ bg: "gray.50" }}
                                >
                                  <Checkbox.Root
                                    checked={config.documentIds.includes(
                                      doc.filename,
                                    )}
                                    onCheckedChange={() =>
                                      toggleDocument(doc.filename)
                                    }
                                  >
                                    <Checkbox.HiddenInput />
                                    <Checkbox.Control borderColor="gray.300" />
                                  </Checkbox.Root>
                                  <Icon
                                    as={FileText}
                                    boxSize={4}
                                    color="gray.400"
                                    flexShrink={0}
                                  />
                                  <Text
                                    fontSize="sm"
                                    color="gray.700"
                                    flex={1}
                                    lineClamp={1}
                                  >
                                    {doc.filename}
                                  </Text>
                                  {doc.validity && (
                                    <Text
                                      fontSize="xs"
                                      color="fg.muted"
                                      flexShrink={0}
                                    >
                                      {doc.validity}
                                    </Text>
                                  )}
                                </Box>
                              ))}
                            </VStack>
                          )}
                        </Box>
                      </VStack>
                    )}
                  </Field.Root>

                  {/* Advanced Settings - Column Configuration */}
                  <Box>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowAdvanced(!showAdvanced)}
                      color="gray.600"
                      fontWeight="medium"
                      fontSize="sm"
                      px={0}
                      _hover={{ bg: "transparent", color: "gray.900" }}
                    >
                      <Icon
                        as={showAdvanced ? ChevronDown : ChevronRight}
                        boxSize={4}
                        mr={2}
                      />
                      Column Configuration
                      <Icon as={Table} boxSize={4} ml={2} />
                    </Button>
                    <Collapsible.Root open={showAdvanced}>
                      <Collapsible.Content asChild>
                        <VStack gap={3} align="stretch" mt={3} pl={2}>
                          <Text fontSize="xs" color="gray.500">
                            Override column names for Excel ground truth files
                            (leave empty for auto-detect)
                          </Text>
                          <Field.Root>
                            <Field.Label
                              fontSize="xs"
                              fontWeight="medium"
                              color="gray.600"
                            >
                              Filename Column
                            </Field.Label>
                            <Input
                              type="text"
                              value={config.columnConfig?.filename || ""}
                              onChange={(e) =>
                                setConfig({
                                  ...config,
                                  columnConfig: {
                                    ...config.columnConfig,
                                    filename: e.target.value || null,
                                    validity:
                                      config.columnConfig?.validity || null,
                                    reason: config.columnConfig?.reason || null,
                                  },
                                })
                              }
                              placeholder="e.g., Document number, filename"
                              borderRadius="sm"
                              borderWidth="1px"
                              borderColor="gray.200"
                              fontSize="sm"
                              size="sm"
                              _hover={{ borderColor: "gray.300" }}
                              _focus={{
                                borderColor: "gray.900",
                                boxShadow: "0 0 0 1px rgba(0, 0, 0, 0.1)",
                              }}
                              _placeholder={{ color: "gray.400" }}
                            />
                          </Field.Root>
                          <Field.Root>
                            <Field.Label
                              fontSize="xs"
                              fontWeight="medium"
                              color="gray.600"
                            >
                              Validity Column
                            </Field.Label>
                            <Input
                              type="text"
                              value={config.columnConfig?.validity || ""}
                              onChange={(e) =>
                                setConfig({
                                  ...config,
                                  columnConfig: {
                                    ...config.columnConfig,
                                    filename:
                                      config.columnConfig?.filename || null,
                                    validity: e.target.value || null,
                                    reason: config.columnConfig?.reason || null,
                                  },
                                })
                              }
                              placeholder="e.g., Valid/Invalid, status"
                              borderRadius="sm"
                              borderWidth="1px"
                              borderColor="gray.200"
                              fontSize="sm"
                              size="sm"
                              _hover={{ borderColor: "gray.300" }}
                              _focus={{
                                borderColor: "gray.900",
                                boxShadow: "0 0 0 1px rgba(0, 0, 0, 0.1)",
                              }}
                              _placeholder={{ color: "gray.400" }}
                            />
                          </Field.Root>
                          <Field.Root>
                            <Field.Label
                              fontSize="xs"
                              fontWeight="medium"
                              color="gray.600"
                            >
                              Reason Column
                            </Field.Label>
                            <Input
                              type="text"
                              value={config.columnConfig?.reason || ""}
                              onChange={(e) =>
                                setConfig({
                                  ...config,
                                  columnConfig: {
                                    ...config.columnConfig,
                                    filename:
                                      config.columnConfig?.filename || null,
                                    validity:
                                      config.columnConfig?.validity || null,
                                    reason: e.target.value || null,
                                  },
                                })
                              }
                              placeholder="e.g., Reason for Invalidity, notes"
                              borderRadius="sm"
                              borderWidth="1px"
                              borderColor="gray.200"
                              fontSize="sm"
                              size="sm"
                              _hover={{ borderColor: "gray.300" }}
                              _focus={{
                                borderColor: "gray.900",
                                boxShadow: "0 0 0 1px rgba(0, 0, 0, 0.1)",
                              }}
                              _placeholder={{ color: "gray.400" }}
                            />
                            <Field.HelperText fontSize="xs" color="fg.muted">
                              For reasoning evaluation, specify the column
                              containing expected reasoning
                            </Field.HelperText>
                          </Field.Root>
                        </VStack>
                      </Collapsible.Content>
                    </Collapsible.Root>
                  </Box>
                </VStack>
              </Dialog.Body>

              <Dialog.Footer
                borderTopWidth="1px"
                borderColor="gray.200"
                gap={3}
                px={6}
                py={3}
                flexShrink={0}
                bg="white"
              >
                <Button
                  variant="ghost"
                  onClick={onClose}
                  borderRadius="sm"
                  color="gray.700"
                  size="sm"
                  fontWeight="medium"
                  _hover={{ bg: "gray.100" }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="solid"
                  bg="gray.900"
                  color="white"
                  borderRadius="sm"
                  size="sm"
                  fontWeight="medium"
                  _hover={{ bg: "gray.800" }}
                >
                  Save Configuration
                </Button>
              </Dialog.Footer>
            </form>
          </Dialog.Content>
        </Dialog.Positioner>
      </Portal>
    </Dialog.Root>
  );
};

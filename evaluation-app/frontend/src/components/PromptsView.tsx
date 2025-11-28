import React, { useState, useEffect } from "react";
import {
  Box,
  Flex,
  VStack,
  HStack,
  Text,
  Heading,
  Button,
  Badge,
  Input,
  Textarea,
  Code,
  Spinner,
} from "@chakra-ui/react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Clock,
  User,
  Edit,
  RotateCcw,
  GitBranch,
  GitCommit,
  Trash2,
} from "lucide-react";
import { PromptSummary, PromptDetails } from "../types";
import { VersionTree } from "./VersionTree";
import { animation, presets } from "@/lib/design-tokens";

interface PromptsViewProps {
  onClose?: () => void;
}

type ViewMode = "content" | "diff";

const MotionBox = motion.create(Box);

export function PromptsView({ onClose }: PromptsViewProps) {
  const [prompts, setPrompts] = useState<PromptSummary[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
  const [promptDetails, setPromptDetails] = useState<PromptDetails | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [showVersionTree, setShowVersionTree] = useState(false);
  const [branchingFromVersion, setBranchingFromVersion] = useState<
    string | null
  >(null);
  const [viewMode, setViewMode] = useState<ViewMode>("content");

  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    try {
      const response = await fetch("/api/prompts");
      if (response.ok) {
        const data = await response.json();
        setPrompts(data.prompts || []);
      }
    } catch (error) {
      console.error("Failed to load prompts:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadPromptDetails = async (promptName: string) => {
    try {
      const response = await fetch(
        `/api/prompts/${encodeURIComponent(promptName)}`,
      );
      if (response.ok) {
        const data = await response.json();
        setPromptDetails(data);
        setEditedContent(data.current_content || "");
        setEditDescription("");
      }
    } catch (error) {
      console.error("Failed to load prompt details:", error);
    }
  };

  const handlePromptSelect = (promptName: string) => {
    setSelectedPrompt(promptName);
    setIsEditing(false);
    setBranchingFromVersion(null);
    setShowVersionTree(false);
    setViewMode("content");
    loadPromptDetails(promptName);
  };

  const handleSaveEdit = async () => {
    if (!selectedPrompt) return;

    // If branching, use branch endpoint
    if (branchingFromVersion) {
      return handleSaveBranch();
    }

    try {
      const response = await fetch(
        `/api/prompts/${encodeURIComponent(selectedPrompt)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: editedContent,
            author: "user",
            description: editDescription || "Updated prompt via UI",
          }),
        },
      );

      if (response.ok) {
        setIsEditing(false);
        loadPromptDetails(selectedPrompt);
        loadPrompts();
        toast.success("Prompt updated");
      } else {
        toast.error("Failed to update prompt");
      }
    } catch (error) {
      console.error("Failed to save prompt:", error);
      toast.error("Error saving prompt");
    }
  };

  const handleDeleteVersion = async (
    versionId: string,
    versionNumber: number,
  ) => {
    if (!selectedPrompt) return;

    // Prevent deleting version 0
    if (versionNumber === 0) {
      toast.error(
        "Cannot delete version 0: The original version cannot be deleted",
      );
      return;
    }

    const confirmed = window.confirm(
      `Delete version ${versionNumber}? This action cannot be undone.`,
    );
    if (!confirmed) return;

    try {
      const response = await fetch(
        `/api/prompts/${encodeURIComponent(selectedPrompt)}/versions/${versionId}`,
        {
          method: "DELETE",
        },
      );

      if (response.ok) {
        loadPromptDetails(selectedPrompt);
        loadPrompts();
        toast.success("Version deleted");
      } else {
        const errorData = await response.json();
        toast.error(
          `Failed to delete version: ${errorData.detail || "Unknown error"}`,
        );
      }
    } catch (error) {
      console.error("Failed to delete version:", error);
      toast.error("Error deleting version");
    }
  };

  const handleActivateVersion = async (versionId: string) => {
    if (!selectedPrompt) return;

    const confirmed = window.confirm(
      "Rollback to this version? This will update the active prompt file.",
    );
    if (!confirmed) return;

    try {
      const response = await fetch(
        `/api/prompts/${encodeURIComponent(selectedPrompt)}/versions/${versionId}/activate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ update_filesystem: true }),
        },
      );

      if (response.ok) {
        loadPromptDetails(selectedPrompt);
        loadPrompts();
        toast.success("Version activated");
      } else {
        toast.error("Failed to activate version");
      }
    } catch (error) {
      console.error("Failed to activate version:", error);
      toast.error("Error activating version");
    }
  };

  const handleCreateSnapshot = async () => {
    if (!selectedPrompt) return;

    try {
      const response = await fetch(
        `/api/prompts/${encodeURIComponent(selectedPrompt)}/snapshot`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            author: "user",
            description: "Manual snapshot via UI",
          }),
        },
      );

      if (response.ok) {
        loadPromptDetails(selectedPrompt);
        loadPrompts();
        toast.success("Snapshot created");
      } else {
        toast.error("Failed to create snapshot");
      }
    } catch (error) {
      console.error("Failed to create snapshot:", error);
    }
  };

  const handleSaveBranch = async () => {
    if (!selectedPrompt || !branchingFromVersion) return;

    try {
      const response = await fetch(
        `/api/prompts/${encodeURIComponent(selectedPrompt)}/branch/${branchingFromVersion}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            content: editedContent,
            author: "user",
            description:
              editDescription ||
              `Branch from ${branchingFromVersion.substring(0, 8)}`,
          }),
        },
      );

      if (response.ok) {
        setIsEditing(false);
        setBranchingFromVersion(null);
        loadPromptDetails(selectedPrompt);
        loadPrompts();
        toast.success("Branch created");
      } else {
        toast.error("Failed to create branch");
      }
    } catch (error) {
      console.error("Failed to create branch:", error);
      toast.error("Error creating branch");
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return new Intl.DateTimeFormat("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(date);
  };

  const getTypeBadgeScheme = (type: string): "subtle" | "solid" => {
    return "subtle";
  };

  if (loading) {
    return (
      <Flex align="center" justify="center" py={16}>
        <VStack gap={3}>
          <Spinner size="xl" color="gray.300" />
          <Text fontSize="sm" color="fg.muted">
            Loading prompts...
          </Text>
        </VStack>
      </Flex>
    );
  }

  return (
    <Flex h="full" gap={6}>
      {/* Prompts List */}
      <VStack w="33%" gap={6} align="stretch">
        <Flex justify="space-between" align="center">
          <Heading size="md" color="fg.emphasis">
            Prompts
          </Heading>
          <Text fontSize="sm" color="fg.muted">
            {prompts.length} total
          </Text>
        </Flex>

        <VStack gap={2} align="stretch">
          <AnimatePresence mode="popLayout">
            {prompts.map((prompt) => (
              <MotionBox
                key={prompt.name}
                {...animation.slideUp}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                <Box
                  as="button"
                  w="full"
                  p={3}
                  borderRadius="lg"
                  border="1px solid"
                  borderColor={
                    selectedPrompt === prompt.name ? "gray.400" : "gray.200"
                  }
                  bg="white"
                  textAlign="left"
                  onClick={() => handlePromptSelect(prompt.name)}
                  boxShadow={
                    selectedPrompt === prompt.name ? "elegant" : undefined
                  }
                  _hover={{
                    boxShadow: "elegant",
                    borderColor: "gray.300",
                  }}
                >
                  <Flex justify="space-between" align="flex-start">
                    <VStack align="flex-start" gap={1} flex={1}>
                      <Text
                        fontSize="sm"
                        fontWeight="medium"
                        color="fg.emphasis"
                        lineClamp={1}
                      >
                        {prompt.name.replace(/_/g, " ")}
                      </Text>
                      <HStack gap={2} fontSize="xs" color="fg.muted">
                        <Badge
                          variant={getTypeBadgeScheme(prompt.type)}
                          borderRadius="md"
                        >
                          {prompt.type}
                        </Badge>
                        {prompt.version_count > 0 && (
                          <Text>{prompt.version_count} versions</Text>
                        )}
                      </HStack>
                    </VStack>
                  </Flex>
                </Box>
              </MotionBox>
            ))}
          </AnimatePresence>
        </VStack>
      </VStack>

      {/* Prompt Details */}
      <VStack flex={1} gap={4} align="stretch">
        {selectedPrompt && promptDetails ? (
          <>
            {/* Header */}
            <Box
              borderRadius="lg"
              border="1px solid"
              borderColor="gray.200"
              bg="white"
              p={4}
            >
              <Flex justify="space-between" align="flex-start">
                <VStack flex={1} align="flex-start" gap={2}>
                  <HStack gap={3} align="center">
                    <Heading size="md" color="fg.emphasis">
                      {selectedPrompt.replace(/_/g, " ")}
                    </Heading>
                    {promptDetails.active_version && (
                      <HStack
                        gap={2}
                        bg="success.100"
                        px={3}
                        py={1}
                        borderRadius="full"
                      >
                        <Box w={2} h={2} bg="success.600" borderRadius="full" />
                        <Text
                          fontSize="xs"
                          fontWeight="medium"
                          color="success.800"
                        >
                          Active Version
                        </Text>
                      </HStack>
                    )}
                  </HStack>
                  <Text fontSize="sm" color="fg.muted">
                    {promptDetails.versions.length}{" "}
                    {promptDetails.versions.length === 1
                      ? "version"
                      : "versions"}{" "}
                    · Last updated{" "}
                    {promptDetails.active_version
                      ? formatDate(promptDetails.active_version.timestamp)
                      : "never"}
                  </Text>
                  {promptDetails.active_version && (
                    <Text fontSize="xs" color="gray.400">
                      Active:{" "}
                      {promptDetails.active_version.version_id.substring(0, 8)}{" "}
                      by {promptDetails.active_version.author}
                    </Text>
                  )}
                </VStack>
                <HStack gap={2}>
                  {!isEditing && viewMode !== "diff" ? (
                    <>
                      <Button
                        size="sm"
                        variant={showVersionTree ? "solid" : "ghost"}
                        onClick={() => setShowVersionTree(!showVersionTree)}
                      >
                        <GitCommit size={14} style={{ marginRight: "6px" }} />
                        Tree
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setIsEditing(true)}
                      >
                        <Edit size={14} style={{ marginRight: "6px" }} />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleCreateSnapshot}
                      >
                        <GitBranch size={14} style={{ marginRight: "6px" }} />
                        Snapshot
                      </Button>
                    </>
                  ) : isEditing ? (
                    <>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setIsEditing(false);
                          setBranchingFromVersion(null);
                          setEditedContent(promptDetails.current_content || "");
                        }}
                      >
                        Cancel
                      </Button>
                      <Button
                        size="sm"
                        variant="solid"
                        onClick={handleSaveEdit}
                      >
                        Save Changes
                      </Button>
                    </>
                  ) : null}
                </HStack>
              </Flex>
            </Box>

            {/* Version Tree or History */}
            {!isEditing &&
              viewMode === "content" &&
              promptDetails.versions.length > 0 && (
                <Box
                  borderRadius="lg"
                  border="1px solid"
                  borderColor="gray.200"
                  bg="white"
                  p={4}
                >
                  <Flex justify="space-between" align="center" mb={3}>
                    <Text {...presets.sectionLabel}>
                      {showVersionTree ? "Version Tree" : "Version History"}
                    </Text>
                    <Text fontSize="xs" color="gray.400">
                      {promptDetails.versions.length}{" "}
                      {promptDetails.versions.length === 1
                        ? "version"
                        : "versions"}
                    </Text>
                  </Flex>

                  {showVersionTree ? (
                    <VersionTree
                      versions={promptDetails.versions}
                      onVersionClick={(version) => {
                        // Could expand to show version details or activate
                      }}
                    />
                  ) : (
                    <VStack gap={2} align="stretch">
                      {promptDetails.versions.map((version) => (
                        <MotionBox
                          key={version.version_id}
                          {...animation.slideDown}
                          transition={{ duration: 0.2 }}
                        >
                          <Box
                            p={3}
                            borderRadius="lg"
                            border="1px solid"
                            borderColor={
                              version.is_active ? "gray.300" : "gray.200"
                            }
                            bg={version.is_active ? "gray.50" : "white"}
                            boxShadow={
                              version.is_active ? "elegant" : undefined
                            }
                            _hover={{
                              borderColor: "gray.300",
                            }}
                          >
                            <Flex justify="space-between" align="flex-start">
                              <VStack flex={1} align="flex-start" gap={1}>
                                <HStack gap={2}>
                                  <Text
                                    fontSize="xs"
                                    fontFamily="mono"
                                    fontWeight="semibold"
                                    color="gray.700"
                                  >
                                    v{version.version_number}
                                  </Text>
                                  <Text
                                    fontSize="xs"
                                    fontFamily="mono"
                                    color="gray.400"
                                  >
                                    {version.version_id.substring(0, 8)}
                                  </Text>
                                  {version.is_active && (
                                    <HStack
                                      gap={1.5}
                                      bg="gray.900"
                                      px={2}
                                      py={0.5}
                                      borderRadius="full"
                                    >
                                      <Box
                                        w={1.5}
                                        h={1.5}
                                        bg="white"
                                        borderRadius="full"
                                      />
                                      <Text
                                        fontSize="xs"
                                        fontWeight="medium"
                                        color="white"
                                      >
                                        Active
                                      </Text>
                                    </HStack>
                                  )}
                                </HStack>
                                <Text fontSize="sm" color="gray.700">
                                  {version.description}
                                </Text>
                                <HStack gap={3} fontSize="xs" color="fg.muted">
                                  <HStack gap={1}>
                                    <User size={12} />
                                    <Text>{version.author}</Text>
                                  </HStack>
                                  <HStack gap={1}>
                                    <Clock size={12} />
                                    <Text>{formatDate(version.timestamp)}</Text>
                                  </HStack>
                                </HStack>
                              </VStack>
                              <HStack gap={2}>
                                <Button
                                  size="xs"
                                  variant="ghost"
                                  onClick={() => {
                                    setIsEditing(true);
                                    setBranchingFromVersion(version.version_id);
                                    setEditedContent(version.content);
                                  }}
                                  title="Create new branch from this version"
                                >
                                  <GitBranch
                                    size={12}
                                    style={{ marginRight: "4px" }}
                                  />
                                  Branch
                                </Button>
                                {!version.is_active && (
                                  <>
                                    <Button
                                      size="xs"
                                      variant="ghost"
                                      onClick={() =>
                                        handleActivateVersion(
                                          version.version_id,
                                        )
                                      }
                                      title="Rollback to this version"
                                    >
                                      <RotateCcw
                                        size={12}
                                        style={{ marginRight: "4px" }}
                                      />
                                      Rollback
                                    </Button>
                                    {version.version_number !== 0 && (
                                      <Button
                                        size="xs"
                                        variant="ghost"
                                        colorPalette="red"
                                        onClick={() =>
                                          handleDeleteVersion(
                                            version.version_id,
                                            version.version_number,
                                          )
                                        }
                                        title="Delete this version"
                                      >
                                        <Trash2
                                          size={12}
                                          style={{ marginRight: "4px" }}
                                        />
                                        Delete
                                      </Button>
                                    )}
                                  </>
                                )}
                              </HStack>
                            </Flex>
                          </Box>
                        </MotionBox>
                      ))}
                    </VStack>
                  )}
                </Box>
              )}

            {/* Content Editor */}
            {viewMode === "content" && (
              <Box
                borderRadius="lg"
                border="1px solid"
                borderColor="gray.200"
                bg="white"
                p={4}
              >
                <Flex justify="space-between" align="center" mb={3}>
                  <Text {...presets.sectionLabel}>
                    {isEditing
                      ? branchingFromVersion
                        ? "Create Branch"
                        : "Edit Content"
                      : "Current Content"}
                  </Text>
                  {isEditing && (
                    <HStack
                      gap={2}
                      bg="gray.100"
                      px={2}
                      py={1}
                      borderRadius="md"
                    >
                      <Box
                        w={1.5}
                        h={1.5}
                        bg={branchingFromVersion ? "gray.600" : "gray.500"}
                        borderRadius="full"
                      />
                      <Text
                        fontSize="xs"
                        fontWeight="medium"
                        color={branchingFromVersion ? "gray.700" : "gray.600"}
                      >
                        {branchingFromVersion
                          ? `Branching from ${branchingFromVersion.substring(0, 8)}`
                          : "Editing - Save to create new version"}
                      </Text>
                    </HStack>
                  )}
                </Flex>
                {isEditing ? (
                  <VStack gap={3} align="stretch">
                    <Textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      fontFamily="mono"
                      fontSize="xs"
                      lineHeight="relaxed"
                      color="gray.700"
                      rows={20}
                      borderWidth="2px"
                      borderColor="gray.200"
                      _hover={{
                        borderColor: "gray.300",
                      }}
                      _focus={{
                        borderColor: "gray.900",
                        boxShadow: "0 0 0 1px gray.900",
                      }}
                    />
                    <Box>
                      <Text
                        fontSize="xs"
                        fontWeight="medium"
                        color="fg.muted"
                        mb={1}
                      >
                        Change Description (required)
                      </Text>
                      <Input
                        value={editDescription}
                        onChange={(e) => setEditDescription(e.target.value)}
                        placeholder="e.g., Improved classification accuracy for floor plans"
                        fontSize="sm"
                        color="gray.700"
                        borderWidth="2px"
                        borderColor="gray.200"
                        _hover={{
                          borderColor: "gray.300",
                        }}
                        _focus={{
                          borderColor: "gray.900",
                          boxShadow: "0 0 0 1px gray.900",
                        }}
                      />
                    </Box>
                  </VStack>
                ) : (
                  <Code
                    display="block"
                    p={4}
                    borderRadius="md"
                    border="1px solid"
                    borderColor="gray.200"
                    bg="gray.50"
                    fontSize="xs"
                    lineHeight="relaxed"
                    color="gray.700"
                    fontFamily="mono"
                    whiteSpace="pre-wrap"
                    overflowX="auto"
                  >
                    {promptDetails.current_content}
                  </Code>
                )}
              </Box>
            )}
          </>
        ) : (
          <Flex
            h="full"
            align="center"
            justify="center"
            borderRadius="lg"
            border="1px dashed"
            borderColor="gray.200"
            bg="gray.50"
          >
            <VStack gap={2}>
              <FileText size={32} color="#D4D4D8" />
              <Text fontSize="sm" fontWeight="medium" color="fg.muted">
                Select a prompt to view details
              </Text>
              <Text fontSize="xs" color="gray.400">
                View content, history, and manage versions
              </Text>
            </VStack>
          </Flex>
        )}
      </VStack>
    </Flex>
  );
}

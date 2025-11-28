import React, { useMemo } from "react";
import { GitBranch, Circle } from "lucide-react";
import { Box, Button, Flex, Text, VStack, Icon, Badge } from "@chakra-ui/react";
import { PromptVersion } from "../types";

interface VersionTreeProps {
  versions: PromptVersion[];
  onVersionClick?: (version: PromptVersion) => void;
}

interface TreeNode {
  version: PromptVersion;
  children: TreeNode[];
  depth: number;
}

export function VersionTree({ versions, onVersionClick }: VersionTreeProps) {
  const tree = useMemo(() => {
    // Build tree structure from versions
    const versionMap = new Map<string, TreeNode>();
    const rootNodes: TreeNode[] = [];

    // Create nodes
    versions.forEach((version) => {
      versionMap.set(version.version_id, {
        version,
        children: [],
        depth: 0,
      });
    });

    // Build parent-child relationships
    versions.forEach((version) => {
      const node = versionMap.get(version.version_id)!;
      if (version.parent_version_id) {
        const parent = versionMap.get(version.parent_version_id);
        if (parent) {
          parent.children.push(node);
          node.depth = parent.depth + 1;
        } else {
          // Parent not found, treat as root
          rootNodes.push(node);
        }
      } else {
        // No parent, this is a root
        rootNodes.push(node);
      }
    });

    // Sort children by timestamp (newest first)
    const sortChildren = (node: TreeNode) => {
      node.children.sort(
        (a, b) =>
          new Date(b.version.timestamp).getTime() -
          new Date(a.version.timestamp).getTime(),
      );
      node.children.forEach(sortChildren);
    };

    rootNodes.forEach(sortChildren);

    // Sort roots by timestamp (newest first)
    rootNodes.sort(
      (a, b) =>
        new Date(b.version.timestamp).getTime() -
        new Date(a.version.timestamp).getTime(),
    );

    return rootNodes;
  }, [versions]);

  const renderNode = (
    node: TreeNode,
    isLast: boolean,
    parentPrefix: string = "",
  ) => {
    const { version, children } = node;
    const hasChildren = children.length > 0;
    const connector = isLast ? "└─" : "├─";
    const prefix = parentPrefix + connector;
    const childPrefix = parentPrefix + (isLast ? "  " : "│ ");

    return (
      <Box key={version.version_id}>
        {/* Current node */}
        <Button
          onClick={() => onVersionClick?.(version)}
          width="full"
          height="auto"
          py={2}
          px={2}
          display="flex"
          alignItems="flex-start"
          gap={2}
          textAlign="left"
          borderRadius="lg"
          bg={version.is_active ? "green.50" : "transparent"}
          _hover={{
            bg: version.is_active ? "green.100" : "gray.50",
          }}
          transition="all 0.15s ease"
          variant="ghost"
        >
          {/* Tree lines */}
          <Text
            fontFamily="mono"
            fontSize="xs"
            color="gray.400"
            whiteSpace="pre"
            display="flex"
            alignItems="center"
            gap={1}
          >
            {prefix}
          </Text>

          {/* Version icon */}
          <Flex
            mt="2px"
            h={5}
            w={5}
            flexShrink={0}
            alignItems="center"
            justifyContent="center"
            borderRadius="full"
            bg={
              version.is_active
                ? "green.600"
                : hasChildren
                  ? "gray.400"
                  : "gray.300"
            }
          >
            {hasChildren ? (
              <Icon as={GitBranch} boxSize={3} color="white" />
            ) : (
              <Icon
                as={Circle}
                boxSize={2}
                color={version.is_active ? "white" : "gray.600"}
                fill={version.is_active ? "white" : "gray.600"}
              />
            )}
          </Flex>

          {/* Version info */}
          <Box minW={0} flex={1}>
            <Flex alignItems="center" gap={2}>
              <Text fontSize="xs" fontFamily="mono" color="gray.600">
                {version.version_id.substring(0, 8)}
              </Text>
              {version.is_active && (
                <Badge
                  bg="green.600"
                  color="white"
                  fontSize="xs"
                  fontWeight="medium"
                  borderRadius="full"
                  px={2}
                  py={0.5}
                >
                  Active
                </Badge>
              )}
            </Flex>
            <Text
              mt={0.5}
              fontSize="xs"
              color="gray.700"
              lineClamp={1}
              lineHeight="short"
            >
              {version.description}
            </Text>
            <Text mt={0.5} fontSize="xs" color="gray.400">
              by {version.author}
            </Text>
          </Box>
        </Button>

        {/* Child nodes */}
        {children.map((child, idx) => (
          <Box key={child.version.version_id} ml={2}>
            {renderNode(child, idx === children.length - 1, childPrefix)}
          </Box>
        ))}
      </Box>
    );
  };

  if (versions.length === 0) {
    return (
      <Flex
        alignItems="center"
        justifyContent="center"
        borderRadius="lg"
        border="1px dashed"
        borderColor="gray.200"
        bg="gray.50"
        p={8}
      >
        <VStack gap={2}>
          <Icon as={GitBranch} boxSize={6} color="gray.300" />
          <Text fontSize="sm" color="gray.500">
            No versions yet
          </Text>
        </VStack>
      </Flex>
    );
  }

  return (
    <VStack gap={1} align="stretch">
      {tree.map((node, idx) => renderNode(node, idx === tree.length - 1))}
    </VStack>
  );
}

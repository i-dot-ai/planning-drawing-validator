import React, { memo } from "react";
import {
  Card,
  Flex,
  HStack,
  VStack,
  Text,
  Badge,
  IconButton,
  Icon,
  Heading,
} from "@chakra-ui/react";
import {
  ArrowLeft,
  Clock,
  CheckCircle2,
  FileText,
  Leaf,
  Droplet,
} from "lucide-react";
import { CarbonImpact } from "../types";

interface RunHeaderProps {
  runId: string;
  startTime: string;
  accuracy?: number;
  modelName?: string;
  totalDocuments?: number;
  cumulativeCarbonImpact?: CarbonImpact | null;
  onClose: () => void;
}

export const RunHeader = memo(function RunHeader({
  runId,
  startTime,
  accuracy,
  modelName,
  totalDocuments,
  cumulativeCarbonImpact,
  onClose,
}: RunHeaderProps) {
  const formatDate = (dateString: string) => {
    if (!dateString) return "Unknown";
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return "Invalid date";

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
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  };

  const formatNumber = (value: number, decimals: number = 6): string => {
    if (value < 0.000001) {
      return value.toExponential(2);
    }
    return value.toFixed(decimals);
  };

  const formatRange = (
    min: number,
    max: number,
    unit: string,
    decimals: number = 6,
  ): string => {
    return `${formatNumber(min, decimals)}-${formatNumber(max, decimals)} ${unit}`;
  };

  const getAccuracyColor = (acc: number) => {
    if (acc >= 90) return "success";
    if (acc >= 70) return "blue";
    return "warning";
  };

  return (
    <Card.Root variant="outline">
      <Card.Body p={6}>
        <Flex align="center" justify="space-between" gap={6}>
          <HStack gap={4} flex={1}>
            {/* Back Button */}
            <IconButton
              aria-label="Back to history"
              onClick={onClose}
              variant="ghost"
              size="md"
            >
              <Icon as={ArrowLeft} boxSize={4} />
            </IconButton>

            {/* Status Icon */}
            <Flex
              align="center"
              justify="center"
              w={8}
              h={8}
              borderRadius="md"
              bg="success.50"
              flexShrink={0}
            >
              <Icon as={CheckCircle2} boxSize={4.5} color="success.600" />
            </Flex>

            {/* Run Info */}
            <VStack align="flex-start" gap={1} flex={1}>
              <HStack gap={2}>
                <Heading size="md">Historical Run</Heading>
                {accuracy !== undefined && (
                  <Badge variant={getAccuracyColor(accuracy) as any}>
                    {accuracy.toFixed(0)}% accuracy
                  </Badge>
                )}
                {modelName && (
                  <Badge
                    borderRadius="full"
                    px={2}
                    py={0.5}
                    fontSize="xs"
                    fontWeight="medium"
                    bg="purple.50"
                    color="purple.600"
                  >
                    {modelName}
                  </Badge>
                )}
              </HStack>

              <HStack gap={3} fontSize="sm" color="fg.muted">
                <HStack gap={1.5}>
                  <Icon as={Clock} boxSize={3.5} />
                  <Text>{formatDate(startTime)}</Text>
                </HStack>

                {totalDocuments !== undefined && (
                  <HStack gap={1.5}>
                    <Icon as={FileText} boxSize={3.5} />
                    <Text>{totalDocuments} documents</Text>
                  </HStack>
                )}
              </HStack>
            </VStack>
          </HStack>

          {/* Cumulative Carbon Impact */}
          {cumulativeCarbonImpact && (
            <Flex
              ml="auto"
              pl={6}
              borderLeftWidth="1px"
              borderLeftColor="border.muted"
            >
              <HStack gap={3}>
                <Flex
                  align="center"
                  justify="center"
                  w={8}
                  h={8}
                  borderRadius="md"
                  bg="success.50"
                >
                  <Icon as={Leaf} boxSize={4.5} color="success.600" />
                </Flex>

                <VStack align="flex-start" gap={1}>
                  <Text
                    fontSize="xs"
                    color="fg.muted"
                    fontWeight="medium"
                    textTransform="uppercase"
                    letterSpacing="wide"
                  >
                    Environmental Impact
                  </Text>

                  <Text
                    fontSize="sm"
                    color="fg.emphasis"
                    fontFamily="mono"
                    fontWeight="medium"
                  >
                    {formatRange(
                      cumulativeCarbonImpact.gwp_kgco2eq_min,
                      cumulativeCarbonImpact.gwp_kgco2eq_max,
                      "kg CO₂",
                      3,
                    )}
                  </Text>
                  <Text fontSize="xs" color="fg.muted" fontFamily="mono">
                    {formatRange(
                      cumulativeCarbonImpact.energy_kwh_min,
                      cumulativeCarbonImpact.energy_kwh_max,
                      "kWh",
                      3,
                    )}
                  </Text>
                  <HStack gap={1}>
                    <Icon as={Droplet} boxSize={3} color="blue.500" />
                    <Text fontSize="xs" color="fg.muted" fontFamily="mono">
                      {formatRange(
                        cumulativeCarbonImpact.wcf_l_min,
                        cumulativeCarbonImpact.wcf_l_max,
                        "L",
                        3,
                      )}
                    </Text>
                  </HStack>
                </VStack>
              </HStack>
            </Flex>
          )}
        </Flex>
      </Card.Body>
    </Card.Root>
  );
});

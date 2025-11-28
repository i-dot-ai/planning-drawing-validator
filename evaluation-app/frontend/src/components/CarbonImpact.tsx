import React, { memo, useState } from "react";
import { Leaf, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { Box, Button, Flex, Text, VStack, Icon, Link } from "@chakra-ui/react";
import { CarbonImpact as CarbonImpactType } from "../types";
import { colors } from "@/lib/design-tokens";

interface CarbonImpactProps {
  impact: CarbonImpactType;
  className?: string;
}

/**
 * Display carbon and environmental impact metrics from LLM inference.
 *
 * Shows energy consumption, global warming potential, abiotic depletion,
 * primary energy usage, and water consumption with min-max ranges due to
 * data centre location variance.
 */
export const CarbonImpactDisplay = memo(function CarbonImpactDisplay({
  impact,
  className,
}: CarbonImpactProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Format number with appropriate precision
  const formatNumber = (value: number, decimals: number = 6): string => {
    if (value < 0.000001) {
      return value.toExponential(2);
    }
    return value.toFixed(decimals);
  };

  // Format range with units
  const formatRange = (
    min: number,
    max: number,
    unit: string,
    decimals: number = 6,
  ): string => {
    return `${formatNumber(min, decimals)} - ${formatNumber(max, decimals)} ${unit}`;
  };

  return (
    <Box
      borderRadius="lg"
      border="1px solid"
      borderColor="gray.200"
      bg="white"
      className={className}
    >
      <Button
        onClick={() => setIsExpanded(!isExpanded)}
        width="full"
        height="auto"
        bg={colors.status.success.bg}
        borderBottom="1px solid"
        borderBottomColor={colors.status.success.border}
        px={4}
        py={2}
        display="flex"
        alignItems="center"
        gap={2}
        _hover={{
          bg: "green.100",
        }}
        transition="all 0.15s ease"
        borderRadius="0"
        borderTopRadius="lg"
        variant="ghost"
        justifyContent="flex-start"
      >
        <Icon as={Leaf} boxSize="4" color={colors.status.success.icon} />
        <Text
          fontSize="xs"
          fontWeight="semibold"
          textTransform="uppercase"
          letterSpacing="wider"
          color={colors.status.success.text}
        >
          Environmental Impact
        </Text>
        <Box ml="auto">
          {isExpanded ? (
            <Icon
              as={ChevronUp}
              boxSize="4"
              color={colors.status.success.icon}
            />
          ) : (
            <Icon
              as={ChevronDown}
              boxSize="4"
              color={colors.status.success.icon}
            />
          )}
        </Box>
      </Button>
      <Box p={4}>
        <VStack gap={3} align="stretch" fontSize="xs">
          {/* Energy Consumption */}
          <Flex justify="space-between" align="baseline">
            <Text color="gray.600" fontWeight="medium">
              Energy
            </Text>
            <Text color="gray.900" fontFamily="mono" textAlign="right">
              {formatRange(
                impact.energy_kwh_min,
                impact.energy_kwh_max,
                "kWh",
                6,
              )}
            </Text>
          </Flex>

          {/* Global Warming Potential (CO2 equivalent) */}
          <Flex
            justify="space-between"
            align="baseline"
            pt={2}
            borderTop="1px solid"
            borderTopColor="gray.100"
          >
            <Text color="gray.600" fontWeight="medium">
              CO₂ Equivalent
            </Text>
            <Text color="gray.900" fontFamily="mono" textAlign="right">
              {formatRange(
                impact.gwp_kgco2eq_min,
                impact.gwp_kgco2eq_max,
                "kgCO₂eq",
                6,
              )}
            </Text>
          </Flex>

          {/* Abiotic Depletion Potential */}
          <Flex
            justify="space-between"
            align="baseline"
            pt={2}
            borderTop="1px solid"
            borderTopColor="gray.100"
          >
            <Text color="gray.600" fontWeight="medium">
              Resource Depletion
            </Text>
            <Text color="gray.900" fontFamily="mono" textAlign="right">
              {formatRange(
                impact.adpe_kgsbeq_min,
                impact.adpe_kgsbeq_max,
                "kgSbeq",
                8,
              )}
            </Text>
          </Flex>

          {/* Primary Energy */}
          <Flex
            justify="space-between"
            align="baseline"
            pt={2}
            borderTop="1px solid"
            borderTopColor="gray.100"
          >
            <Text color="gray.600" fontWeight="medium">
              Primary Energy
            </Text>
            <Text color="gray.900" fontFamily="mono" textAlign="right">
              {formatRange(impact.pe_mj_min, impact.pe_mj_max, "MJ", 6)}
            </Text>
          </Flex>

          {/* Water Consumption */}
          <Flex
            justify="space-between"
            align="baseline"
            pt={2}
            borderTop="1px solid"
            borderTopColor="gray.100"
          >
            <Text color="gray.600" fontWeight="medium">
              Water Consumption
            </Text>
            <Text color="gray.900" fontFamily="mono" textAlign="right">
              {formatRange(impact.wcf_l_min, impact.wcf_l_max, "L", 6)}
            </Text>
          </Flex>
        </VStack>

        {/* Explanatory note */}
        <Text
          mt={3}
          pt={3}
          borderTop="1px solid"
          borderTopColor="gray.100"
          fontSize="10px"
          color="gray.500"
          lineHeight="relaxed"
        >
          Ranges reflect variance in data centre energy sources and efficiency.
          Metrics tracked via ecologits library from LLM inference.
        </Text>

        {/* Expandable information section */}
        {isExpanded && (
          <VStack
            mt={4}
            pt={4}
            borderTop="1px solid"
            borderTopColor="gray.200"
            gap={3}
            align="stretch"
            fontSize="xs"
          >
            <Box>
              <Text fontWeight="semibold" color="gray.700" mb={2}>
                How environmental impact is estimated
              </Text>
            </Box>

            <Box>
              <Text color="gray.600" lineHeight="relaxed">
                <Text as="strong" color="gray.700">
                  Methodology:
                </Text>{" "}
                The{" "}
                <Link
                  href="https://github.com/genai-impact/ecologits"
                  target="_blank"
                  rel="noopener noreferrer"
                  display="inline-flex"
                  alignItems="center"
                  gap={0.5}
                  color={colors.status.success.icon}
                  _hover={{
                    color: colors.status.success.text,
                  }}
                  textDecoration="underline"
                  fontWeight="medium"
                >
                  ecologits
                  <Icon as={ExternalLink} boxSize="3.5" />
                </Link>{" "}
                library estimates environmental impact based on LLM model
                parameters, token usage, and data centre efficiency metrics.
              </Text>
            </Box>

            <Box>
              <Text color="gray.600" lineHeight="relaxed">
                <Text as="strong" color="gray.700">
                  Data sources:
                </Text>{" "}
                Impact factors derived from academic research on LLM
                environmental costs and provider specifications.
              </Text>
            </Box>

            <Box>
              <Text color="gray.600" lineHeight="relaxed">
                <Text as="strong" color="gray.700">
                  Min/Max ranges:
                </Text>{" "}
                Different data centres have varying energy sources (coal vs
                renewable) and Power Usage Effectiveness (PUE) ratios, resulting
                in impact ranges rather than single values.
              </Text>
            </Box>

            <Box>
              <Text color="gray.700" fontWeight="medium" mb={1.5}>
                Metrics tracked:
              </Text>
              <Box
                as="ul"
                ml={6}
                color="gray.600"
                display="flex"
                flexDirection="column"
                gap={0.5}
              >
                <Box as="li" display="list-item" listStyleType="disc">
                  Energy consumption (kWh)
                </Box>
                <Box as="li" display="list-item" listStyleType="disc">
                  CO₂ equivalent emissions (kgCO₂eq)
                </Box>
                <Box as="li" display="list-item" listStyleType="disc">
                  Abiotic resource depletion (kgSbeq)
                </Box>
                <Box as="li" display="list-item" listStyleType="disc">
                  Primary energy usage (MJ)
                </Box>
                <Box as="li" display="list-item" listStyleType="disc">
                  Water consumption factor (L)
                </Box>
              </Box>
            </Box>
          </VStack>
        )}
      </Box>
    </Box>
  );
});

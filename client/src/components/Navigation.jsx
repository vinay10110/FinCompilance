import { Box, Flex, Text, useColorModeValue, HStack, IconButton, Tooltip } from '@chakra-ui/react'
import { SignedIn, SignedOut, useClerk, UserButton, useUser } from '@clerk/clerk-react'
import { Button } from '@chakra-ui/react'
import { FiSettings, FiArrowLeft } from 'react-icons/fi'
import { FaSlack } from 'react-icons/fa'
import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import WorkflowDialog from './WorkflowDialog'

const Navigation = () => {
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const { openSignIn } = useClerk()
  const { user } = useUser()
  const navigate = useNavigate()
  const location = useLocation()
  const [isWorkflowDialogOpen, setIsWorkflowDialogOpen] = useState(false)
  
  // Check if we're on a workflow page
  const isOnWorkflowPage = location.pathname.startsWith('/workflows/')
  
  // Slack channel invite link from environment variables
  const handleSlackJoin = () => {
    const slackInviteUrl = import.meta.env.VITE_SLACK_INVITE_URL
    window.open(slackInviteUrl, '_blank')
  }

  return (
    <Box
      as="nav"
      bg={bgColor}
      borderBottom="1px"
      borderColor={borderColor}
      position="fixed"
      top={0}
      left={0}
      right={0}
      zIndex={1000}
      boxShadow="sm"
    >
      <Flex
        maxW="100%"
        mx="auto"
        px={6}
        py={4}
        align="center"
        justify="space-between"
      >
        <HStack spacing={3}>
          {isOnWorkflowPage && (
            <Tooltip label="Back to Home">
              <IconButton
                icon={<FiArrowLeft />}
                variant="ghost"
                onClick={() => navigate('/')}
                aria-label="Back to home"
                size="sm"
              />
            </Tooltip>
          )}
          <Text fontSize="xl" fontWeight="bold">
            AI Compliance Assistant
          </Text>
        </HStack>

        <HStack spacing={4}>
          <SignedIn>
            <Tooltip label="Join our Slack community for updates and discussions">
              <Button
                variant="outline"
                leftIcon={<FaSlack />}
                onClick={handleSlackJoin}
                colorScheme="purple"
                size="sm"
              >
                Join Slack
              </Button>
            </Tooltip>
            <Button
              variant="ghost"
              leftIcon={<FiSettings />}
              onClick={() => setIsWorkflowDialogOpen(true)}
            >
              Workflows
            </Button>
            <UserButton afterSignOutUrl="/"/>
          </SignedIn>
          <SignedOut>
            <Tooltip label="Join our Slack community for updates and discussions">
              <Button
                variant="outline"
                leftIcon={<FaSlack />}
                onClick={handleSlackJoin}
                colorScheme="purple"
                size="sm"
                mr={2}
              >
                Join Slack
              </Button>
            </Tooltip>
            <Button onClick={() => openSignIn()} colorScheme="blue">
              Sign In
            </Button>
          </SignedOut>
        </HStack>
      </Flex>

      {/* Workflow Dialog */}
      <WorkflowDialog
        isOpen={isWorkflowDialogOpen}
        onClose={() => setIsWorkflowDialogOpen(false)}
        userId={user?.id || "default_user"}
      />
    </Box>
  )
}

export default Navigation
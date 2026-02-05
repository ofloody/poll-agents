/** Entry point for Poll Agents server. */

import { loadSettings } from "./config/settings";
import { createRepositories } from "./repository/factory";
import { PollAgentsServer } from "./server";

function main(): void {
  const settings = loadSettings();
  const [questionSetRepo, responseRepo] = createRepositories(settings);

  const server = new PollAgentsServer(settings, questionSetRepo, responseRepo);
  server.start();
}

main();

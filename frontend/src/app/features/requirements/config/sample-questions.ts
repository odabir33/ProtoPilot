import { Question } from '../models/question.model';

export const REQUIREMENTS_QUESTION_FLOW: Question[] = [
  // {
  //   id: 'project_name',
  //   label: 'What is the name of your project?',
  //   inputType: 'text',
  // },
  // {
  //   id: 'problem_statement',
  //   label: 'What problem are you trying to solve?',
  //   inputType: 'text',
  // },
  // {
  //   id: 'target_users',
  //   label: 'Who are your target users?',
  //   inputType: 'multi-select',
  //   suggestions: [{label: 'Admins', selected: false}, {label: 'End Users', selected: false}, {label: 'Managers', selected: false}],
  // }
];

export enum CONSTANTS {
  REQUIREMENTS_AGENT_NAME = "requirements",
  REQUIREMENTS_AGENT_URL = "http://127.0.0.1:8000/chat",
  REQUIREMENTS_INITIAL_PROMPT = "Hi, What are you trying to build today?"
}
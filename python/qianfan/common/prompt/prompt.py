# Copyright (c) 2023 Baidu, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import json
import re
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, cast

from qianfan.common.hub.interface import HubSerializable
from qianfan.config import encoding
from qianfan.consts import (
    PromptFrameworkType,
    PromptSceneType,
    PromptScoreStandard,
    PromptType,
)
from qianfan.errors import InvalidArgumentError, RequestError
from qianfan.resources.console.prompt import Prompt as PromptResource
from qianfan.resources.llm.completion import Completion
from qianfan.resources.typing import Literal, QfResponse

if TYPE_CHECKING:
    from qianfan.dataset import Dataset
from qianfan.utils import log_info, log_warn


@dataclass
class PromptLabel(HubSerializable):
    """
    Class of prompt label
    """

    id: Union[str, int]
    """
    id of the label
    """
    name: str
    """
    name of the label
    """
    color: str
    """
    the color displayed in the console
    """


class Prompt(HubSerializable):
    """
    Prompt
    """

    id: Optional[str] = None
    name: Optional[str] = None
    template: str
    variables: List[str]
    identifier: Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"]
    labels: List[PromptLabel]
    type: PromptType
    scene_type: PromptSceneType
    framework_type: PromptFrameworkType
    negative_template: Optional[str] = None
    negative_variables: Optional[List[str]] = None
    creator_name: Optional[str] = None
    _mode: str

    def __init__(
        self,
        template: Optional[str] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
        identifier: Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"] = "{}",
        variables: Optional[List[str]] = None,
        labels: List[PromptLabel] = [],
        type: PromptType = PromptType.User,
        scene_type: PromptSceneType = PromptSceneType.Text2Text,
        framework_type: PromptFrameworkType = PromptFrameworkType.NotUse,
        negative_template: Optional[str] = None,
        negative_variables: Optional[List[str]] = None,
        creator_name: Optional[str] = None,
    ) -> None:
        """
        Initializes a Prompt object.

        Parameters:
          template (Optional[str]):
            The template string for the prompt, required if mode id "local".
          name (Optional[str]):
            The name of the prompt, required if mode is "remote".
          id (Optional[int]):
            The id of the prompt on platform.
          identifier (Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"]):
            The identifier format used in the template, e.g., "{}", "{{}}", "[]".
          variables (Optional[List[str]]):
            A list of variables used in the prompt template. SDK will extract them
            if not specified.
          labels (List[PromptLabel]):
            A list of labels associated with the prompt.
          type (PromptType):
            The type of the prompt, e.g., PromptType.User.
          scene_type (PromptSceneType):
            The scene type of the prompt, e.g., PromptSceneType.Text2Text.
          framework_type (PromptFrameworkType):
            The framework type used in the prompt, e.g., PromptFrameworkType.Fewshot.
          negative_template (Optional[str]):
            The negative template string for the prompt.
          negative_variables (Optional[List[str]]):
            A list of variables used in the negative template. SDK will extract them
            if not specified.
          creator_name (Optional[str]):
            The name of the creator of the prompt.
        """
        self.id = id
        self.name = name
        if template is None:
            raise InvalidArgumentError("template is required if using local prompt")
        self.template = template
        self.identifier = identifier
        self.labels = labels
        self.type = type
        self.scene_type = scene_type
        self.framework_type = framework_type
        if variables is not None:
            self.variables = variables
        else:
            self.variables = PromptResource._extract_variables(template, identifier)
        self.negative_template = negative_template
        if self.negative_template is not None:
            # if user does not provide negative varibles
            # extract them from negative template
            if self.negative_variables is not None:
                self.negative_variables = negative_variables
            else:
                self.negative_variables = PromptResource._extract_variables(
                    self.negative_template, identifier
                )
        self.creator_name = creator_name
        self._mode = "local"

    @classmethod
    def _hub_pull(cls, name: str) -> "Prompt":
        """
        Init the prompt from api by name.
        """
        resp = PromptResource.list(name=name, type=PromptType.User)
        prompt_info = None
        # try to find the prompt in user prompts
        for item in resp["result"]["items"]:
            if item["templateName"] == name:
                prompt_info = item
                break
        # if not found, try to find the prompt in preset prompts
        if prompt_info is None:
            resp = PromptResource.list(name=name, type=PromptType.Preset)
            for item in resp["result"]["items"]:
                if item["templateName"] == name:
                    prompt_info = item
                    break
        # if still not found, raise error
        if prompt_info is None:
            raise InvalidArgumentError(f"Prompt `{name}` does not exist")

        prompt = cls(
            name=prompt_info["templateName"],
            id=prompt_info["templatePK"],
            template=prompt_info["templateContent"],
            variables=(
                []
                if prompt_info["templateVariables"] == ""
                else prompt_info["templateVariables"].split(",")
            ),
            labels=[
                PromptLabel(label["labelId"], label["labelName"], label["color"])
                for label in prompt_info["labels"]
            ],
            identifier=prompt_info["variableIdentifier"],
            type=PromptType(prompt_info["type"]),
            scene_type=PromptSceneType(prompt_info["sceneType"]),
            framework_type=PromptFrameworkType(prompt_info["frameworkType"]),
            creator_name=prompt_info["creatorName"],
        )
        if prompt.scene_type == PromptSceneType.Text2Image:
            prompt.negative_template = prompt_info["negativeTemplateContent"]
            # sometimes negativeTemplateVariables is not set in api response
            if "negativeTemplateVariables" in prompt_info:
                prompt.negative_variables = prompt_info[
                    "negativeTemplateVariables"
                ].split(",")
            else:
                prompt.negative_variables = []
        prompt._mode = "remote"
        return prompt

    @classmethod
    def from_file(
        cls,
        path: str,
        identifier: Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"] = "{}",
    ) -> "Prompt":
        """
        Create a Prompt object from file. The file should only contain the
        prompt template.

        Parameters:
          path (str):
            The path of the prompt file.
          identifier (Literal["{}", "{{}}", "[]", "[[]]", "()", "(())"]):
            The identifier of the prompt.
        """
        with open(path, "r", encoding=encoding()) as f:
            content = f.read()
        return cls(template=content, identifier=identifier)

    def save_to_file(self, path: str) -> None:
        """
        Save the prompt template to file.

        Parameters:
          path (str):
            The path of the prompt file.
        """
        with open(path, "w", encoding=encoding()) as f:
            f.write(self.template)

    def _hub_push(self) -> None:
        """
        Upload the prompt to Qianfan. If the prompt is local, it will create a new one
        on the server. Otherwise, it will update the existing prompt.
        """
        # local prompt, create it
        if self._mode == "local" or self.id is None:
            if self.name is None:
                raise InvalidArgumentError(
                    "name is required when uploading to the server"
                )
            resp = PromptResource.create(
                name=self.name,
                template=self.template,
                identifier=self.identifier,
                scene=self.scene_type,
                framework=self.framework_type,
                label_ids=[label.id for label in self.labels],
                negative_template=self.negative_template,
                negative_variables=self.negative_variables,
            )
            if not resp["success"]:
                raise InvalidArgumentError(
                    f"Failed to create prompt: {resp['message']['global']}"
                )
            self.id = resp["result"]["templatePK"]
            self._mode = "remote"
        else:
            if self.name is None:
                raise InvalidArgumentError(
                    "name is required when uploading to the server"
                )
            resp = PromptResource.update(
                id=self.id,
                name=self.name,
                label_ids=[label.id for label in self.labels],
                template=self.template,
                identifier=self.identifier,
                negative_template=self.negative_template,
            )
            if not resp["success"]:
                raise InvalidArgumentError(
                    f"Failed to update prompt: {resp['message']['global']}"
                )
            self.id = resp["result"]["templatePK"]

    def render(self, **kwargs: str) -> Tuple[str, Optional[str]]:
        """
        Render the prompt with given variables.

        Parameters:
          kwargs (Any):
            The value of the variables to be used for variable replacement in the
            template.
        """
        prompt = self.template
        left_id, right_id = PromptResource._split_identifier(self.identifier)
        for v in self.variables:
            if v not in kwargs:
                raise InvalidArgumentError(f"variable `{v}` is not provided")
            prompt = prompt.replace(f"{left_id}{v}{right_id}", str(kwargs[v]))
        neg_prompt = None
        if self.negative_template is not None:
            if self.negative_variables is None:
                self.negative_variables = []
            neg_prompt = self.negative_template
            for v in self.negative_variables:
                if v not in kwargs:
                    raise InvalidArgumentError(f"variable `{v}` is not provided")
                neg_prompt = neg_prompt.replace(
                    f"{left_id}{v}{right_id}", str(kwargs[v])
                )
        return prompt, neg_prompt

    def delete(self) -> None:
        """
        Delete the prompt from Qianfan.
        """
        if self._mode == "local" or self.id is None:
            log_warn("local prompt does not need to be deleted")
            return
        if self.type == PromptType.Preset:
            log_warn(f"preset prompt {self.name} cannot be deleted")
            return
        resp = PromptResource.delete(id=self.id)
        if not resp["success"]:
            raise InvalidArgumentError(
                f"Failed to delete prompt: {resp['message']['global']}"
            )
        self.id = None
        self._mode = "local"

    def set_template(self, template: str) -> None:
        """
        Set the prompt's template. The variables in the template will be extracted.

        Parameters:
          template (str):
            The new template.
        """
        self.template = template
        self.variables = PromptResource._extract_variables(template, self.identifier)

    def set_negative_template(self, template: str) -> None:
        """
        Set the prompt's negative template. The variables in the template will be
        extracted.

        Parameters:
          template (str):
            The new negative template.
        """
        self.negative_template = template
        self.negative_variables = PromptResource._extract_variables(
            template, self.identifier
        )

    def _hub_serialize(self) -> Dict[str, Any]:
        """
        Implement `HubSerializable` protocol.
        Convert the prompt to a dictionary that can be used for serialization.
        """
        dic = super()._hub_serialize()
        del dic["args"]["_mode"]
        del dic["args"]["id"]
        return dic

    @classmethod
    def _hub_deserialize(cls, dic: Dict[str, Any]) -> "Prompt":
        """
        Implement `HubSerializable` protocol.
        Convert a dictionary to a prompt.
        """
        return cls(**dic)

    @classmethod
    def base_prompt(
        cls,
        prompt: str,
        background: str = "",
        additional_data: str = "",
        output_schema: str = "",
    ) -> str:
        """
        Generates a base type prompt for language models.

        Parameters:
          prompt (str):
            The main text prompt that defines the task or query for the language model.
          background (str, optional):
            Additional context or background information to provide more context to the
            model.
          additional_data (str, optional):
            Extra data that can be included to enhance the specificity or details of
            the prompt.
          output_schema (str, optional):
            The desired schema for formatting the output of the language model.

        Please refer to the following link for more details about CRISPE prompt.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Zlo55g7t3
        """
        prompt = f"指令:{prompt}"
        background = f"背景信息:{background}" if background != "" else ""
        additional_data = f"补充数据:{additional_data}" if additional_data != "" else ""
        output_schema = f"输出格式:{output_schema}" if output_schema != "" else ""
        return "\n".join([prompt, background, additional_data, output_schema])

    @classmethod
    def crispe_prompt(
        cls,
        statement: str,
        capacity: str = "",
        insight: str = "",
        personality: str = "",
        experiment: str = "",
    ) -> str:
        """
        Generates a CRISPE-type prompt for fine-tuning models.

        Parameters:
          statement (str):
            The main task that the model should focus on.
          capacity (str, optional):
            Capacity information specifying what role you want the model to play.
          insight (str, optional):
            Insights or guidance to provide additional context for the fine-tuning task.
          personality (str, optional):
            The output style or personality of the model.
          experiment (str, optional):
            The limit of the output range of the model.

        Please refer to the following link for more details about CRISPE prompt.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Hlo56qd21
        """
        prompt_list = []
        if capacity != "":
            prompt_list.append(f"能力与角色：{capacity}")
        if insight != "":
            prompt_list.append(f"背景信息：{insight}")
        if statement != "":
            prompt_list.append(f"指令：{statement}")
        if personality != "":
            prompt_list.append(f"输出风格：{personality}")
        if experiment != "":
            prompt_list.append(f"输出范围：{experiment}")
        return "\n".join(prompt_list)

    @classmethod
    def fewshot_prompt(
        cls,
        prompt: str = "",
        examples: List[Tuple[str, str]] = [],
    ) -> str:
        """
        Generates a few-shot prompt for model input.

        Parameters:
          prompt (str):
            The main prompt that sets the context for what task should the model
            focus on.
          examples (List[Tuple[str, str]]):
            A list of example tuples, where each tuple contains a model input string
            and its corresponding expected output. These examples help the model
            understand the desired behavior.

        Please refer to the following link for more details about fewshot prompt.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Nlo57dbf4

        """
        if len(examples) == 0:
            raise InvalidArgumentError("At least one example is required.")
        examples_prompt = [f"输入:{inp}\n输出:{outp}" for inp, outp in examples]
        output = "\n\n".join(examples_prompt)
        if prompt != "":
            output = prompt + "\n\n" + output
        return output

    def optimize(
        self,
        optimize_quality: bool = True,
        simplify_prompt: bool = False,
        iteration_round: Literal[1, 2] = 1,
        enable_cot: bool = False,
        app_id: Optional[int] = None,
        service_name: Optional[str] = None,
        **kwargs: Any,
    ) -> "Prompt":
        """
        Optimize a prompt for better performance and effectiveness.

        Parameters:
          optimize_quality (bool):
            Flag indicating whether to optimize for prompt quality.
          simplify_prompt (bool):
            Flag indicating whether to simplify the prompt structure.
          iteration_round (Literal[1, 2]):
            The number of optimization iterations to perform (1 or 2).
          enable_cot (bool):
            Flag indicating whether to enable chain of thought.
          app_id (Optional[int]):
            Optional application ID for context-specific optimizations.
          service_name (Optional[str]):
            Optional service used for optimizing.
          **kwargs (Any):
            Additional keyword arguments for future extensibility.

        Returns:
          Prompt:
            The optimized Prompt object.

        Please refer to the following link for more details about prompt optimization.

        API Doc: https://cloud.baidu.com/doc/WENXINWORKSHOP/s/olr8svd33
        """
        operations = []
        operations.append(
            {
                "opType": 1,
                "payload": 1 if optimize_quality else 0,
            }
        )
        operations.append(
            {
                "opType": 2,
                "payload": 1 if simplify_prompt else 0,
            }
        )
        operations.append({"opType": 3, "payload": iteration_round})
        operations.append(
            {
                "opType": 4,
                "payload": 1 if enable_cot else 0,
            }
        )
        resp = PromptResource.create_optimiztion_task(
            self.template,
            operations,
            app_id=app_id,
            service_name=service_name,
            **kwargs,
        )
        task_id = resp["result"]["id"]
        while True:
            resp = PromptResource.get_optimization_task(task_id, **kwargs)
            status = resp["result"]["processStatus"]
            if status == 2:  # fininished
                break
            elif status == 3:  # failed
                raise RequestError("Prompt optimization task failed.")
            time.sleep(1)
        optimized_prompt = resp["result"]["optimizeContent"]

        return Prompt(optimized_prompt, identifier=self.identifier)

    def apo_by_sample(
        self,
        example: Optional["Dataset"] = None,
        sample_prompt: Optional["Prompt"] = None,
        feedback_prompt: Optional["Prompt"] = None,
        update_prompt: Optional["Prompt"] = None,
        iteration_round: int = 3,
        infer_config: Dict[str, Any] = {"model": "ERNIE-Speed"},
        optimize_config: Dict[str, Any] = {"model": "ERNIE-4.0-8K"},
    ) -> "Prompt":
        if iteration_round < 1:
            raise ValueError("iteration_round must be greater than or equal to 1.")
        if len(self.variables) > 0 and example is None:
            raise ValueError("Example is required when there are variables in prompt.")

        from qianfan.common.prompt.template import (
            PROMPT_OPTIMIZE_FEEDBACK_TMPL,
            PROMPT_OPTIMIZE_SAMPLE_TMPL,
            PROMPT_OPTIMIZE_SAMPLE_WO_OUTPUT_TMPL,
            PROMPT_OPTIMIZE_UPDATE_TMPL,
        )
        from qianfan.resources.llm.chat_completion import ChatCompletion

        if sample_prompt is None:
            if example is None:
                sample_prompt = Prompt(
                    PROMPT_OPTIMIZE_SAMPLE_WO_OUTPUT_TMPL, identifier="{{}}"
                )
            else:
                sample_prompt = Prompt(PROMPT_OPTIMIZE_SAMPLE_TMPL, identifier="{{}}")
        if feedback_prompt is None:
            feedback_prompt = Prompt(PROMPT_OPTIMIZE_FEEDBACK_TMPL, identifier="{{}}")
        if update_prompt is None:
            update_prompt = Prompt(PROMPT_OPTIMIZE_UPDATE_TMPL, identifier="{{}}")

        client = ChatCompletion()
        left_identifier, right_identifier = PromptResource._split_identifier(
            self.identifier
        )
        current_prompt = self

        for _ in range(iteration_round):
            sample_prompts: List[str]
            # use prompt to generate sample output
            if example is not None:
                dataset_infer_config = copy.deepcopy(infer_config)
                if "model" in infer_config:
                    dataset_infer_config["service_model"] = infer_config["model"]
                    del dataset_infer_config["model"]
                if "endpoint" in infer_config:
                    dataset_infer_config["service_endpoint"] = infer_config["endpoint"]
                    del dataset_infer_config["endpoint"]
                samples = example.test_using_llm(
                    prompt_template=current_prompt, **dataset_infer_config
                )
                sample_prompts = [
                    sample_prompt.render(
                        input=json.dumps(
                            {k: sample[k] for k in self.variables},
                            ensure_ascii=False,
                            indent=4,
                        ),
                        expect=sample["expected_output"],
                        response=sample["llm_output"],
                    )[0]
                    for sample in samples.list()
                ]
            else:
                model_output = ChatCompletion().do(
                    messages=[{"role": "user", "content": current_prompt.render()[0]}],
                    **infer_config,
                )
                assert isinstance(model_output, QfResponse)
                sample_prompts = [
                    sample_prompt.render(
                        input=current_prompt.render()[0],
                        expect="",
                        response=model_output["result"],
                    )[0]
                ]
            sample_str = "\n===\n".join(sample_prompts)
            # put sample output into feedback prompt
            feedback_input = feedback_prompt.render(
                current_prompt=current_prompt.template,
                samples=sample_str,
            )[0]
            log_info(f"Feedback input: {repr(feedback_input)}")
            # get feedback from model
            feedback = client.do(
                messages=[
                    {
                        "role": "user",
                        "content": feedback_input,
                    }
                ],
                **optimize_config,
            )
            assert isinstance(feedback, QfResponse)
            log_info(f"Feedback output: {repr(feedback['result'])}")
            # use model to update prompt
            update_input = update_prompt.render(
                current_prompt=current_prompt.template,
                samples=sample_str,
                feedback=feedback["result"],
                variables=" ".join(
                    [
                        f"{left_identifier}{var}{right_identifier}"
                        for var in self.variables
                    ]
                ),
            )[0]
            log_info(f"Update input: {repr(update_input)}")
            update_resp = client.do(
                messages=[
                    {
                        "role": "user",
                        "content": update_input,
                    }
                ],
                **optimize_config,
            )
            assert isinstance(update_resp, QfResponse)
            update = update_resp["result"]

            log_info(f"Update output: {repr(update)}")

            # update prompt
            try:
                new_prompt_tmpl = re.findall(
                    "<START>(.*)<END>", update, re.MULTILINE | re.DOTALL
                )[0]
            except Exception:
                new_prompt_tmpl = update
            log_info(f"New prompt: {repr(new_prompt_tmpl)}")
            current_prompt = Prompt(new_prompt_tmpl, identifier=self.identifier)
        return current_prompt

    def simplify(
        self,
        simplify_prompt: Optional["Prompt"] = None,
        config: Dict[str, Any] = {"model": "ERNIE-4.0-8K"},
    ) -> "Prompt":
        from qianfan.common.prompt.template import PROMPT_SIMPLIFY_TMPL

        if simplify_prompt is None:
            simplify_prompt = Prompt(PROMPT_SIMPLIFY_TMPL, identifier="{{}}")

        left_identifier, right_identifier = PromptResource._split_identifier(
            self.identifier
        )
        client = Completion()
        resp = client.do(
            simplify_prompt.render(
                current_prompt=self.template,
                variables=" ".join(
                    [
                        f"{left_identifier}{var}{right_identifier}"
                        for var in self.variables
                    ]
                ),
            )[0],
            **config,
        )
        assert isinstance(resp, QfResponse)
        output = resp["result"]
        try:
            new_prompt_tmpl = re.findall(
                "<START>(.*)<END>", output, re.MULTILINE | re.DOTALL
            )[0]
        except Exception:
            new_prompt_tmpl = output
        return Prompt(new_prompt_tmpl, identifier=self.identifier)

    @dataclass
    class PromptEvaluateResult(object):
        """
        Evaluation result of a prompt
        """

        prompt: "Prompt"
        scene: List[Dict[str, Any]]
        summary: str

    @classmethod
    def evaluate(
        cls,
        prompt_list: List["Prompt"],
        scenes: List[Dict[str, Any]],
        model: Completion,
        standard: PromptScoreStandard = PromptScoreStandard.Semantic,
    ) -> List[PromptEvaluateResult]:
        """
        Evaluate a list of prompts against specified scenes using the given model.

        Parameters:
          prompt_list (List["Prompt"]):
            A list of prompt templates to be evaluated.
          scenes (List[Dict[str, Any]]):
            List of scenes represented as dictionaries containing relevant information.
            The dict should contain the following keys:
              - args: A dict containing the variables to be replaced in the prompt.
              - expected: The expected output of the prompt.
          client (Completion):
            An instance of the Completion client.
          standard (PromptScoreStandard, optional):
            The scoring standard to be used for evaluating prompts.

        Returns:
          List[PromptEvaluateResult]:
            A list of evaluation results, each containing the original prompt, the
            result of each scene, and a summary string.

        Example:
        result_list = PromptEvaluateResult.evaluate(
            prompt_list=[prompt1, prompt2, prompt3],
            scenes=[{
                "args": {"name": "Alice"},
                "expected": "Hello, Alice!"
            }],
            client=Completion(model="ERNIE-4.0-8K"),
            standard=PromptScoreStandard.Semantic
        )
        """
        results = [
            Prompt.PromptEvaluateResult(
                scene=[
                    {
                        "new_prompt": prompt.render(**scene["args"])[0],
                        "variables": scene["args"],
                        "expected_target": scene["expected"],
                    }
                    for scene in scenes
                ],
                prompt=prompt,
                summary="",
            )
            for prompt in prompt_list
        ]

        for i in range(len(results)):
            for j in range(len(results[i].scene)):
                resp = cast(QfResponse, model.do(results[i].scene[j]["new_prompt"]))
                results[i].scene[j]["response"] = resp["result"]

        eval_summary_req = [
            {
                "prompt": prompt.prompt.template,
                "scenes": [
                    {
                        "variables": scene["variables"],
                        "expected_target": scene["expected_target"],
                        "response": scene["response"],
                        "new_prompt": scene["new_prompt"],
                    }
                    for scene in prompt.scene
                ],
                "response_list": [r["response"] for r in prompt.scene],
            }
            for prompt in results
        ]

        eval_score_req = [
            {
                "scene": scenes[j]["expected"],
                "response_list": [
                    results[i].scene[j]["response"] for i in range(len(prompt_list))
                ],
            }
            for j in range(len(scenes))
        ]

        summary_resp = PromptResource.evaluation_summary(eval_summary_req)
        summary = summary_resp["result"]["responses"]

        for i in range(len(results)):
            results[i].summary = summary[i]["response"]

        score_resp = PromptResource.evaluation_score(standard.value, eval_score_req)
        score = score_resp["result"]["scores"]

        for i in range(len(results)):
            for j in range(len(results[i].scene)):
                results[i].scene[j]["score"] = score[j][i]

        return results

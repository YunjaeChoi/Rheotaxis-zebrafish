import * as React from "react";
import * as Immutable from "immutable";
import { connect } from "react-redux";
import { actions, selectors } from "@nteract/core";
import {
  Outputs
} from "@nteract/presentational-components";
import {
  KernelOutputError,
  Output,
  StreamText
} from "@nteract/outputs";
import TransformMedia from "@nteract/notebook-app-component/transform-media";
import {
  AppState,
  ContentRef,
} from "@nteract/types";
import { CellId } from "@nteract/commutable";
import {
  Segment,
} from 'semantic-ui-react'
import 'semantic-ui-css/semantic.min.css'

const emptyList = Immutable.List();

type DisplayProps = DisplayStateProps & DisplayOwnProps;

interface DisplayOwnProps {
  cellToDisplay: number;
  expanded: boolean;
  hidden: boolean;
}

interface DisplayStateProps {
  id: CellId;
  contentRef: ContentRef;
  outputs: Immutable.List<any>;
}

class OutDisplay extends React.Component<DisplayProps> {

  render() {
    let disp;
    if (this.props.outputs === null){
      disp = null;
    }
    else{
      disp = (
        <Outputs
          hidden={this.props.hidden}
          expanded={this.props.expanded}
        >
          {this.props.outputs.map((output, index) => (
            <Output output={output} key={index}>
              <TransformMedia
                output_type={"display_data"}
                cellId={this.props.id}
                contentRef={this.props.contentRef}
                index={index}
              />
              <TransformMedia
                output_type={"execute_result"}
                cellId={this.props.id}
                contentRef={this.props.contentRef}
                index={index}
              />
              <KernelOutputError />
              <StreamText />
            </Output>
          ))}
        </Outputs>
      );
    }
    return (
      <Segment >
        {disp}
      </Segment>
    );
  }
}

const makeMapStateToProps = (
  initialState: AppState,
  { contentRef }: { contentRef: ContentRef }
) => {
  if (!contentRef) {
    throw new Error("<Notebook /> has to have a contentRef");
  }

  const mapStateToProps = (state: AppState, ownProps: DisplayOwnProps): DisplayStateProps => {
    const content = selectors.content(state, { contentRef });
    const model = selectors.model(state, { contentRef });

    if (!model || !content) {
      throw new Error(
        "<Notebook /> has to have content & model that are notebook types"
      );
    }

    if (model.type !== "notebook") {
      return {
        id: null,
        contentRef,
        outputs: null
      };
    }

    const id = model.notebook.cellOrder.get(ownProps.cellToDisplay)

    const cell = selectors.notebook.cellById(model, { id });
    if (!cell) {
      throw new Error("cell not found inside cell map");
    }

    const outputs = cell.get("outputs", emptyList);

    return {
      id,
      contentRef,
      outputs
    };
  };

  return mapStateToProps;
};

export const OutputDisplay = connect(makeMapStateToProps)(OutDisplay);
